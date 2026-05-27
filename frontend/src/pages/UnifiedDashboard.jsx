import { useState } from "react";
import "../styles/dashboard.css";

import KrishiBot from "./KrishiBot";
import DrishtiScan from "./DrishtiScan";
import MandiPredict from "./MandiPredict";
import YieldSense from "./YieldSense";

export default function UnifiedDashboard() {

const [active,setActive]=useState("krishibot");

return (

<div className="dashboard-page">

<div className="app">

<aside className="sidebar">

<div className="sidebar-logo">
<h2>🌱 KRISHIDRISHTI AI</h2>
<p>Unified Dashboard</p>
</div>

<div className="sidebar-nav">

<button
className={`nav-item ${active==="krishibot"?"active":""}`}
onClick={()=>setActive("krishibot")}
>
🤖 KrishiBot
</button>

<button
className={`nav-item ${active==="drishti"?"active":""}`}
onClick={()=>setActive("drishti")}
>
📷 DrishtiScan
</button>

<button
className={`nav-item ${active==="mandi"?"active":""}`}
onClick={()=>setActive("mandi")}
>
📈 MandiPredict
</button>

<button
className={`nav-item ${active==="yield"?"active":""}`}
onClick={()=>setActive("yield")}
>
🌾 YieldSense
</button>

</div>

</aside>

<div className="main-panel">

{active==="krishibot" && <KrishiBot/>}
{active==="drishti" && <DrishtiScan/>}
{active==="mandi" && <MandiPredict/>}
{active==="yield" && <YieldSense/>}

</div>

</div>

</div>

);

}