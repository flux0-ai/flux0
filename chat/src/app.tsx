import { Button } from "@/components/ui/button";
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

  return <Button variant="secondary">{JSON.stringify(data)}</Button>;
}

export default App;
