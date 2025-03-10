import { useEffect, useState } from "react";

function App() {
  const [data, setData] = useState<unknown>(null);

  useEffect(() => {
    const fetchData = async () => {
      const response = await fetch("/api/agents");
      const result = (await response.json()) as unknown;
      setData(result);
    };

    fetchData().catch(console.error);
  }, []);

  return <div>{JSON.stringify(data)}</div>;
}

export default App;
