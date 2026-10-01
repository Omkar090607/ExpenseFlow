const S=window.SUMMARY,P=["#6366f1","#22d3ee","#f59e0b","#ef4444","#10b981","#ec4899","#94a3b8"];
Chart.defaults.color="#cbd5e1";Chart.defaults.borderColor="rgba(255,255,255,.08)";
const mk=(id,cfg,has)=>{const c=document.getElementById(id);if(!c)return;if(!has){c.replaceWith(Object.assign(document.createElement("p"),{className:"text-secondary",textContent:"No data yet."}));return}new Chart(c,cfg)};
const cats=Object.keys(S.categories),months=Object.keys(S.monthly),yb={y:{beginAtZero:true}},nl={legend:{display:false}};
mk("catChart",{type:"doughnut",data:{labels:cats,datasets:[{data:Object.values(S.categories),backgroundColor:P,borderWidth:0}]},options:{cutout:"65%",plugins:{legend:{position:"bottom"}}}},cats.length);
mk("monthChart",{type:"bar",data:{labels:months,datasets:[{label:"₹ spent",data:Object.values(S.monthly),backgroundColor:"#6366f1",borderRadius:8}]},options:{plugins:nl,scales:yb}},months.length);
mk("dayChart",{type:"line",data:{labels:Object.keys(S.daily),datasets:[{label:"₹ per day",data:Object.values(S.daily),borderColor:"#22d3ee",backgroundColor:"rgba(34,211,238,.15)",fill:true,tension:.35}]},options:{plugins:nl,scales:yb}},true);
