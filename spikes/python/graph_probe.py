"""P00 human-input checkpoint probe with SQLite or a dedicated test Postgres database."""

import argparse
import os
from contextlib import contextmanager
from pathlib import Path
from typing import TypedDict

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class ReportState(TypedDict, total=False):
    title: str
    answer: str
    status: str


def ask_student(state: ReportState) -> ReportState:
    answer = interrupt({"title": state["title"], "question": "Which method did you use?"})
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("An answer is required")
    return {"answer": answer.strip(), "status": "resumed"}


@contextmanager
def open_checkpointer(sqlite_path: str):
    database = os.getenv("P00_TEST_CHECKPOINT_DATABASE_URL")
    if database:
        with PostgresSaver.from_conn_string(database) as saver:
            saver.setup()
            yield saver
    else:
        Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)
        with SqliteSaver.from_conn_string(sqlite_path) as saver:
            yield saver


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("pause", "resume"))
    parser.add_argument("--sqlite", default=".p00-output/checkpoints.sqlite")
    parser.add_argument("--thread", required=True, help="Use the same fresh ID for pause and resume")
    parser.add_argument("--answer")
    args = parser.parse_args()
    if args.stage == "resume" and (not args.answer or not args.answer.strip()):
        parser.error("resume requires --answer")
    config = {"configurable": {"thread_id": args.thread}}
    graph = StateGraph(ReportState)
    graph.add_node("ask_student", ask_student)
    graph.add_edge(START, "ask_student")
    graph.add_edge("ask_student", END)
    with open_checkpointer(args.sqlite) as saver:
        app = graph.compile(checkpointer=saver)
        if args.stage == "pause":
            result = app.invoke({"title": "Reading habits", "status": "waiting"}, config)
            assert result["__interrupt__"][0].value["question"] == "Which method did you use?"
            assert "answer" not in result
            assert app.get_state(config).next == ("ask_student",)
            print("PAUSED: checkpoint saved; process exiting.")
        else:
            previous = app.get_state(config)
            assert previous.next == ("ask_student",), "Expected a saved, interrupted run"
            result = app.invoke(Command(resume=args.answer), config)
            assert result == {"title": "Reading habits", "status": "resumed", "answer": args.answer.strip()}
            assert not app.get_state(config).next
            print("RESUMED: second process loaded the checkpoint and completed.")


if __name__ == "__main__":
    main()
