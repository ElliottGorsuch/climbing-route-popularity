/* Static route explorer. No users, personal histories, or inferred tick totals. */
'use strict';
const $ = id => document.getElementById(id);
const fmt = n => Number(n).toLocaleString('en-US', {maximumFractionDigits:1});
const colors = {Sport:'#287f8e', Trad:'#d08042', Bouldering:'#6d67a0'};
const escapeHtml = s => String(s ?? '').replace(/[&<>"']/g, x => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
const unpack = payload => payload.rows.map(row => Object.fromEntries(payload.columns.map((key,i) => [key,row[i]])));
let routes = [], filtered = [], pca = null, map = null, layers = null, activeCell = null;
const CELL = .2;
const cellKey = r => `${Math.floor(r.area_latitude/CELL)},${Math.floor(r.area_longitude/CELL)}`;
function matching(r) {
  const term = $('search').value.trim().toLowerCase();
  const length = $('length').value;
  return ($('type').value === 'all' || r.analysis_type === $('type').value)
    && ($('state').value === 'all' || r.state === $('state').value)
    && ($('grade').value === 'all' || r.analysis_grade_family === $('grade').value)
    && ($('risk').value === 'all' || r.protection_group === $('risk').value)
    && (!term || `${r.route_name} ${r.state}`.toLowerCase().includes(term))
    && (length === 'all' || (length === 'unknown' ? r.length_feet === null :
      r.length_feet !== null && (length === 'short' ? r.length_feet <= 100 :
      length === 'medium' ? r.length_feet > 100 && r.length_feet <= 300 : r.length_feet > 300)));
}
function updateGrades() {
  const old = $('grade').value;
  const subset = routes.filter(r => ($('type').value === 'all' || r.analysis_type === $('type').value)
    && ($('state').value === 'all' || r.state === $('state').value));
  const grades = [...new Map(subset.filter(r => r.analysis_grade_family).map(r => [r.analysis_grade_family, r.grade_order])).entries()]
    .sort((a,b) => a[0].startsWith('5.') === b[0].startsWith('5.') ? a[1]-b[1] : a[0].startsWith('5.') ? -1 : 1);
  $('grade').replaceChildren(new Option('All grades','all'), ...grades.map(([g]) => new Option(g,g)));
  if (grades.some(([g]) => g === old)) $('grade').value = old;
}
function cellValue(cell, metric) {
  if(metric === 'mean') return cell.ticks / cell.routes.length;
  if(metric === 'routes') return cell.routes.length;
  if(metric === 'climbers') return cell.climbers;
  return cell.ticks;
}
function dominant(styles) {
  const ranking = Object.entries(styles).sort((a,b) => b[1]-a[1]);
  return ranking[0][1] === ranking[1][1] ? 'Tie' : ranking[0][0];
}
function renderMap() {
  layers.clearLayers();
  const cells = new Map();
  for(const r of filtered) {
    if(!r.analysis_map_valid || !Number.isFinite(r.area_latitude) || !Number.isFinite(r.area_longitude)) continue;
    const key = cellKey(r);
    if(!cells.has(key)) cells.set(key,{ticks:0, climbers:0, styles:{Sport:0,Trad:0,Bouldering:0}, routes:[]});
    const cell = cells.get(key);
    cell.ticks += r.ticks; cell.climbers += r.climbers; cell.styles[r.analysis_type] += r.ticks; cell.routes.push(r);
  }
  const metric = $('metric').value;
  const values = [...cells.values()].map(c => cellValue(c,metric));
  const maximum = Math.max(1,...values);
  for(const [key, cell] of cells) {
    const [lat,lon] = key.split(',').map(Number);
    const weight = Math.log1p(cellValue(cell,metric))/Math.log1p(maximum);
    const leading = dominant(cell.styles);
    const color = metric === 'style' ? colors[leading] || '#77828b' : `hsl(155 29% ${86 - 65*weight}%)`;
    const rect = L.rectangle([[lat*CELL,lon*CELL],[(lat+1)*CELL,(lon+1)*CELL]],
      {color, weight:.5, fillColor:color, fillOpacity:.72}).addTo(layers);
    const summary = Object.entries(cell.styles).map(([s,n]) => `${s}: ${fmt(n)} ticks`).join('<br>');
    rect.bindTooltip(`${fmt(cell.routes.length)} routes · ${fmt(cell.ticks)} sample ticks`);
    rect.bindPopup(`<strong>Recorded activity in this cell</strong><br>${fmt(cell.routes.length)} routes<br>${fmt(cell.ticks)} sample ticks<br>${fmt(cell.ticks/cell.routes.length)} mean ticks / route<br>${summary}<br><small>Matching routes are shown in the table below.</small>`);
    rect.on('click', () => {activeCell=key; renderTable(); $('clearCell').hidden=false; $('selection').textContent=`Selected cell: ${fmt(cell.routes.length)} routes. Use the table to open a route.`;});
  }
  const labels = {ticks:'Total sample ticks',mean:'Mean sample ticks per route',routes:'Recorded routes',climbers:'Route–climber pairs',style:'Leading climbing style by sample ticks'};
  $('mapHeading').textContent=labels[metric];
  $('mapExplanation').textContent = metric === 'style' ? 'Cell colors show which style has the most sample ticks. A tie is gray. Filter by state or grade to explore how the mix changes.' :
    metric === 'mean' ? 'Each cell shows average sample ticks per matching route. Small route counts can produce unstable averages; click cells to inspect their counts.' :
    metric === 'climbers' ? 'Distinct climbers are counted per route, then summed. The same person may contribute to several routes; this is not a count of distinct people in an area.' :
    'Each cell adds matching route records. More recorded activity may reflect more routes, reporting habits or source coverage. Click a cell to inspect its routes.';
  $('legend').innerHTML = metric === 'style' ? Object.entries(colors).map(([k,c]) => `<span class="chip" style="background:${c}"></span>${k} &nbsp; `).join('') + '<span class="chip" style="background:#77828b"></span>Tie' :
    `${labels[metric]} · 0 <span class="gradient"></span> ${fmt(maximum)} · log color scale · empty cells = no matching records`;
}
function renderTable() {
  const selected=activeCell ? filtered.filter(r=>cellKey(r)===activeCell) : filtered;
  $('tableHeading').textContent=activeCell ? 'Most recorded routes in the selected cell' : 'Most recorded routes in this selection';
  const top = [...selected].sort((a,b)=>b.ticks-a.ticks).slice(0,25);
  $('routeRows').innerHTML=top.length ? top.map(r=>`<tr><td><a href="${escapeHtml(r.route_url)}" target="_blank" rel="noopener">${escapeHtml(r.route_name || 'Unnamed route')} ↗</a></td><td>${escapeHtml(r.state)}</td><td><span class="chip" style="background:${colors[r.analysis_type]}"></span>${r.analysis_type}</td><td>${escapeHtml(r.analysis_grade_family || 'Unresolved')}</td><td>${fmt(r.ticks)}</td><td>${fmt(r.climbers)}</td><td>${r.length_feet === null ? '—' : fmt(r.length_feet)}</td></tr>`).join('') : '<tr><td colspan="7">No routes match these filters.</td></tr>';
}
function refresh(fit=false) {
  filtered=routes.filter(matching); activeCell=null; $('clearCell').hidden=true; $('selection').textContent='';
  const total=filtered.reduce((n,r)=>n+r.ticks,0);
  $('routeCount').textContent=fmt(filtered.length); $('tickCount').textContent=fmt(total);
  $('stateCount').textContent=new Set(filtered.map(r=>r.state)).size;
  $('styleSummary').innerHTML=Object.entries(colors).map(([kind,color])=>{
    const subset=filtered.filter(r=>r.analysis_type===kind); const ticks=subset.reduce((n,r)=>n+r.ticks,0);
    const share=total ? 100*ticks/total : 0;
    return `<div class="styleitem"><span class="chip" style="background:${color}"></span><strong>${kind}</strong> · ${fmt(share)}% of ticks<br>${fmt(subset.length)} routes · ${fmt(ticks)} ticks<div class="bar" style="width:${share}%;background:${color}"></div></div>`;
  }).join('');
  renderMap(); renderTable(); if(fit) fitRoutes();
}
function fitRoutes() {
  const coords=filtered.filter(r=>r.analysis_map_valid&&Number.isFinite(r.area_latitude)&&Number.isFinite(r.area_longitude)).map(r=>[r.area_latitude,r.area_longitude]);
  if(coords.length) map.fitBounds(L.latLngBounds(coords),{padding:[25,25],maxZoom:12});
}
function pcaDraw() {
  if(!pca) return;
  const width=850,height=550,pad=70;
  const x=v=>pad+(v+4.5)/9*(width-2*pad), y=v=>height-pad-(v+4.5)/9*(height-2*pad);
  const ratio=pca.metadata.explained_variance_ratio;
  let svg='<defs><marker id="arrow" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="#24453b"/></marker></defs>';
  for(let v=-4;v<=4;v+=2) svg+=`<line x1="${x(v)}" x2="${x(v)}" y1="${pad}" y2="${height-pad}" stroke="#e2e8e5"/><line x1="${pad}" x2="${width-pad}" y1="${y(v)}" y2="${y(v)}" stroke="#e2e8e5"/><text x="${x(v)}" y="${height-pad+22}" text-anchor="middle" fill="#66747c" font-size="12">${v}</text><text x="${pad-15}" y="${y(v)+4}" text-anchor="end" fill="#66747c" font-size="12">${v}</text>`;
  const maxTicks=Math.max(1,...pca.points.map(r=>r.ticks));
  const shown=pca.points.filter(r=>Math.abs(r.pc1)<=4.5&&Math.abs(r.pc2)<=4.5);
  for(const r of shown) {
    const color=$('pcaColor').value==='style' ? colors[r.analysis_type] : `hsl(${170-110*Math.log1p(r.ticks)/Math.log1p(maxTicks)} 50% 42%)`;
    svg+=`<circle class="point" data-id="${r.mp_route_id}" cx="${x(r.pc1)}" cy="${y(r.pc2)}" r="2.5" fill="${color}" opacity=".4"><title>${escapeHtml(r.route_name)} · ${r.analysis_type} · ${fmt(r.ticks)} sample ticks</title></circle>`;
  }
  const names={log_length:'Log length',log_pitches:'Log pitches',grade_order:'YDS family',average_stars:'Kaggle stars',is_pg13:'PG-13 recorded',is_r:'R recorded',is_x:'X recorded'};
  const labelPositions={log_length:[2.85,.05],log_pitches:[2.85,-1.25],grade_order:[.3,2.95],average_stars:[1.55,2.25],is_pg13:[-2.8,-1.3],is_r:[-1.7,-2.05],is_x:[.25,-2.55]};
  pca.loadings.forEach(a=>{const pos=labelPositions[a.feature];svg+=`<line x1="${x(0)}" y1="${y(0)}" x2="${x(a.PC1*3)}" y2="${y(a.PC2*3)}" stroke="#24453b" stroke-width="1.5" marker-end="url(#arrow)"/><line x1="${x(a.PC1*3)}" y1="${y(a.PC2*3)}" x2="${x(pos[0])}" y2="${y(pos[1])}" stroke="#71847d" stroke-dasharray="2 3"/><text x="${x(pos[0])}" y="${y(pos[1])}" font-size="11" fill="#24453b" stroke="white" stroke-width="3" paint-order="stroke">${names[a.feature]}</text>`;});
  svg+=`<text x="${width/2}" y="${height-12}" text-anchor="middle" fill="#66747c">PC1 · unit-SD scores (${(ratio[0]*100).toFixed(1)}% variance)</text><text transform="translate(18 ${height/2}) rotate(-90)" text-anchor="middle" fill="#66747c">PC2 · unit-SD scores (${(ratio[1]*100).toFixed(1)}% variance)</text>`;
  $('pcaPlot').innerHTML=svg;
  $('pcaLegend').innerHTML=$('pcaColor').value==='style' ? ['Sport','Trad'].map(k=>`<span class="chip" style="background:${colors[k]}"></span>${k} &nbsp; `).join('') : `Sample ticks · 0 <span class="gradient" style="background:linear-gradient(90deg,hsl(170 50% 42%),hsl(60 50% 42%))"></span> ${fmt(maxTicks)} · log color scale`; 
  $('pcaCaption').textContent=`Fit: ${fmt(pca.metadata.fit_routes)} complete sport/trad routes. Plot: ${fmt(shown.length)} visible points from a fixed ${fmt(pca.points.length)}-route sample; some scores lie outside ±4.5. PC1 + PC2 preserve ${((ratio[0]+ratio[1])*100).toFixed(1)}% of feature variance. Arrows ×3.`;
  $('pcaPlot').querySelectorAll('.point').forEach(node=>node.addEventListener('click',()=>{
    const r=pca.points.find(r=>r.mp_route_id===node.dataset.id);
    $('pcaDetail').innerHTML=`<strong>${escapeHtml(r.route_name)}</strong><br>${escapeHtml(r.state)} · ${r.analysis_type}<br>${fmt(r.ticks)} sample ticks · ${fmt(r.climbers)} sampled climbers<br>PC1 ${r.pc1.toFixed(2)} · PC2 ${r.pc2.toFixed(2)}`;
  }));
}
document.querySelectorAll('nav button').forEach(button=>button.addEventListener('click',()=>{
  document.querySelectorAll('.page').forEach(page=>page.hidden=page.id!==button.dataset.page);
  document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b===button));
  if(button.dataset.page==='atlas'&&map) map.invalidateSize(); if(button.dataset.page==='pca') pcaDraw();
}));
async function init() {
  if(typeof L==='undefined') throw new Error('The map library could not load. Check your internet connection and reload.');
  const responses=await Promise.all([fetch('data/routes.json'),fetch('data/pca.json')]);
  if(responses.some(r=>!r.ok)) throw new Error('Route exports are missing. Run python scripts/eda.py, then serve the web directory.');
  const [payload,projection]=await Promise.all(responses.map(r=>r.json()));
  routes=unpack(payload); pca={...projection,points:unpack(projection)};
  [...new Set(routes.map(r=>r.state))].sort().forEach(state=>$('state').add(new Option(state,state)));
  map=L.map('map',{preferCanvas:true,scrollWheelZoom:false}).setView([39,-98],4);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'}).addTo(map);
  layers=L.layerGroup().addTo(map); L.control.scale().addTo(map);
  for(const id of ['type','state','grade','metric','risk','length']) $(id).addEventListener('change',()=>{if(id==='type'||id==='state') updateGrades();refresh(id==='state');});
  let timer; $('search').addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(()=>refresh(),160);});
  $('reset').addEventListener('click',()=>{['type','state','grade','risk','length'].forEach(id=>$(id).value='all');$('metric').value='ticks';$('search').value='';updateGrades();refresh();map.setView([39,-98],4);});
  $('fit').addEventListener('click',fitRoutes);
  $('clearCell').addEventListener('click',()=>{activeCell=null;$('clearCell').hidden=true;$('selection').textContent='';renderTable();});
  $('pcaColor').addEventListener('change',pcaDraw);
  $('download').addEventListener('click',()=>{
    const columns=['mp_route_id','route_name','state','analysis_type','analysis_grade_family','ticks','climbers','length_feet','pitches','protection_group'];
    const csv=[columns.join(','),...filtered.map(r=>columns.map(c=>'"'+String(r[c]??'').replaceAll('"','""')+'"').join(','))].join('\n');
    const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='climbing_filtered_sample.csv';a.click();URL.revokeObjectURL(url);
  });
  updateGrades();refresh();$('loadStatus').textContent=`Loaded ${fmt(routes.length)} core rock routes. Default map view shows the contiguous U.S.; Alaska and Hawaii are included and available through the state filter. ${routes.filter(r=>!r.analysis_map_valid).length} route omitted from maps due to implausible U.S. coordinates.`;
}
init().catch(error=>{$('loadStatus').textContent=error.message;console.error(error);});
