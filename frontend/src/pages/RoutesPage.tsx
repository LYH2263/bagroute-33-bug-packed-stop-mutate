import { useEffect, useState } from "react";
import { api } from "../api/client";
type R = { id: number; name: string; max_weight_kg: number; max_volume_l: number };
export default function RoutesPage() {
  const [rows, setRows] = useState<R[]>([]);
  useEffect(() => { api<R[]>("/routes").then(setRows); }, []);
  return (<>
    <h2>路线</h2>
    <table className="table"><thead><tr><th>名称</th><th>重量上限 kg</th><th>体积上限 L</th></tr></thead>
    <tbody>{rows.map(r => <tr key={r.id}><td>{r.name}</td><td className="mono">{r.max_weight_kg}</td><td className="mono">{r.max_volume_l}</td></tr>)}</tbody></table>
  </>);
}
