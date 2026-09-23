import { useEffect, useState } from "react";
import { api } from "../api/client";
type Bag = { id: number; route_id: number; bag_index: number; weight_kg: number; volume_l: number; items: { stop_name: string; weight_kg: number; volume_l: number }[] };
export default function BagsPage() {
  const [rows, setRows] = useState<Bag[]>([]);
  useEffect(() => { api<Bag[]>("/bags").then(setRows); }, []);
  return (<>
    <h2>袋明细</h2>
    <p className="hint">袋内数值以当前落库袋行为准。</p>
    <table className="table"><thead><tr><th>路线</th><th>袋号</th><th>重量</th><th>体积</th><th>订户</th></tr></thead>
    <tbody>{rows.map(b => <tr key={b.id}><td>{b.route_id}</td><td>{b.bag_index}</td><td className="mono">{b.weight_kg}</td><td className="mono">{b.volume_l}</td>
      <td>{b.items.map(i => i.stop_name).join(" → ")}</td></tr>)}
      {!rows.length && <tr><td colSpan={5}>尚无装袋结果，请先执行装袋</td></tr>}
    </tbody></table>
  </>);
}
