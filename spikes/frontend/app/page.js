import Image from "next/image";

export default function Page() {
  return <main>
    <h1>Acadence P00</h1>
    <p>Local compatibility fixture</p>
    <Image src="/fixture.svg" width={40} height={40} alt="Sample report cover" unoptimized />
  </main>;
}
