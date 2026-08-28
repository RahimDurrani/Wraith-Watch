
import { useState, useEffect, useCallback } from "react";

export function useFetch(url) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    fetch(url)
      .then(r => r.json())
      .then(d => { setData(d);  setLoading(false); })
      .catch(() => setLoading(false));
  }, [url]);

  useEffect(() => { load(); }, [load]);

  return { data, loading, reload: load };
}
