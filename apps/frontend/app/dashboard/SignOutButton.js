export default function SignOutButton() {
  return (
    <form action="/api/auth/logout" className="sign-out-control" method="post">
      <button
        className="acadence-button-primary"
        type="submit"
      >
        Sign out
      </button>
    </form>
  );
}
