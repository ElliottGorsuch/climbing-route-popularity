/* Static route explorer. No users, personal histories, or inferred tick totals. */
'use strict';
const $ = id => document.getElementById(id);
const fmt = n => Number(n).toLocaleString('en-US', {maximumFractionDigits:1});
const colors = {Sport:'#287f8e', Trad:'#d08042', Bouldering:'#6d67a0'};
const escapeHtml = s => String(s ?? '').replace(/[&<>"']/g, x => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
const unpack = payload => payload.rows.map(row => Object.fromEntries(payload.columns.map((key,i) => [key,row[i]])));
let routes = [], filtered = [], pca = null, map = null, layers = null, activeCell = null, tableLimit = 25, routeById = new Map();
let CELL = .2;
const selectedGrades = new Set();
let availableGrades = [];
const cellKey = r => `${Math.floor(r.area_latitude/CELL)},${Math.floor(r.area_longitude/CELL)}`;
function matching(r) {
  const term = $('search').value.trim().toLowerCase();
  const length = $('length').value;
  return ($('type').value === 'all' || r.analysis_type === $('type').value)
    && ($('state').value === 'all' || r.state === $('state').value)
    && (!selectedGrades.size || selectedGrades.has(r.analysis_grade_family))
    && ($('risk').value === 'all' || r.protection_group === $('risk').value)
    && (!term || `${r.route_name} ${r.state}`.toLowerCase().includes(term))
    && (length === 'all' || (length === 'unknown' ? r.length_feet === null :
      r.length_feet !== null && (length === 'short' ? r.length_feet <= 100 :
      length === 'medium' ? r.length_feet > 100 && r.length_feet <= 300 : r.length_feet > 300)));
}
function updateGrades() {
  const subset = routes.filter(r => $('type').value === 'all' || r.analysis_type === $('type').value);
  availableGrades = [...new Map(subset.filter(r => r.analysis_grade_family).map(r => [r.analysis_grade_family, r.grade_order])).entries()]
    .sort((a,b) => a[0].startsWith('5.') === b[0].startsWith('5.') ? a[1]-b[1] : a[0].startsWith('5.') ? -1 : 1);
  for (const g of selectedGrades) if (!availableGrades.some(([grade]) => grade === g)) selectedGrades.delete(g);
  $('gradeChips').innerHTML = availableGrades.map(([g]) => `<button class="gradechip ${g.startsWith('5.') ? 'yds' : 'vscale'}" data-grade="${escapeHtml(g)}" aria-pressed="${selectedGrades.has(g)}">${escapeHtml(g)}</button>`).join('');
  $('gradeChips').querySelectorAll('button').forEach(button => button.addEventListener('click', () => {
    const g = button.dataset.grade;
    if (selectedGrades.has(g)) selectedGrades.delete(g); else selectedGrades.add(g);
    updateGradeSummary(); refresh();
  }));
  if ($('type').value === 'Bouldering') $('gradeScale').value = 'v';
  else if ($('type').value !== 'all') $('gradeScale').value = 'yds';
  updateRangeOptions(); updateGradeSummary();
}
function updateGradeSummary() {
  const selected = availableGrades.filter(([g]) => selectedGrades.has(g)).map(([g]) => g);
  $('gradeSummary').textContent = selected.length ? selected.join(', ') : 'All grades';
  $('gradeChips').querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', selectedGrades.has(b.dataset.grade)));
  $('gradeMessage').textContent = selected.length ? `Only ${selected.join(', ')} are included.` : 'All grades included, including unresolved grades.';
}
function updateRangeOptions() {
  const grades = availableGrades.filter(([g]) => $('gradeScale').value === 'yds' ? g.startsWith('5.') : g.startsWith('V'));
  for (const id of ['gradeFrom','gradeTo']) $(id).replaceChildren(...grades.map(([g]) => new Option(g,g)));
  if (grades.length) $('gradeTo').value = grades.at(-1)[0];
  $('applyRange').disabled = !grades.length;
}
function routeDetail(r) {
  const value = (n, suffix = '') => n == null ? 'Not recorded' : fmt(n) + suffix;
  return `<h3>${escapeHtml(r.route_name || 'Unnamed route')}</h3><p>${escapeHtml(r.state)} · <span class="stylebadge" style="--badge:${colors[r.analysis_type]}">${r.analysis_type}</span></p>
    <dl class="routestats"><div><dt>Grade family</dt><dd>${escapeHtml(r.analysis_grade_family || 'Unresolved')}</dd></div><div><dt>Original grade</dt><dd>${escapeHtml(r.rating_raw || 'Not recorded')}</dd></div><div><dt>Pitches</dt><dd>${value(r.pitches)}</dd></div><div><dt>Length</dt><dd>${value(r.length_feet, ' ft')}</dd></div><div><dt>Historical valid ratings</dt><dd>${value(r.rating_valid_count)}</dd></div><div><dt>Protection</dt><dd>${escapeHtml(r.protection_group)}</dd></div><div><dt>Sample ticks</dt><dd>${fmt(r.ticks)}</dd></div><div><dt>Sampled climbers</dt><dd>${fmt(r.climbers)}</dd></div></dl>
    <a class="mpbutton" href="${escapeHtml(r.route_url)}" target="_blank" rel="noopener">Open Mountain Project ↗</a>`;
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
    rect.on('click', () => {activeCell=key; tableLimit=25; renderTable(); $('clearCell').hidden=false; $('selection').textContent=`Selected cell: ${fmt(cell.routes.length)} routes. Use the table to open a route.`;});
  }
  const labels = {ticks:'Total sample ticks',mean:'Mean sample ticks per route',routes:'Recorded routes',climbers:'Route–climber pairs',style:'Leading climbing style by sample ticks'};
  $('cellNote').textContent=`Cells are ${CELL}° latitude × longitude`;
  $('mapHeading').textContent=labels[metric];
  $('mapExplanation').textContent = metric === 'style' ? 'Cell colors show which style has the most sample ticks. A tie is gray. Filter by state or grade to explore how the mix changes.' :
    metric === 'mean' ? 'Each cell shows average sample ticks per matching route. Small route counts can produce unstable averages; click cells to inspect their counts.' :
    metric === 'climbers' ? 'Distinct climbers are counted per route, then summed. The same person may contribute to several routes; this is not a count of distinct people in an area.' :
    'Each cell adds matching route records. More recorded activity may reflect more routes, reporting habits or source coverage. Click a cell to inspect its routes.';
  $('legend').innerHTML = metric === 'style' ? Object.entries(colors).map(([k,c]) => `<span class="chip" style="background:${c}"></span>${k} &nbsp; `).join('') + '<span class="chip" style="background:#77828b"></span>Tie' :
    `${labels[metric]} · 0 <span class="gradient"></span> ${fmt(maximum)} · log color scale · empty cells = no matching records`;
}
function tableRoutes() {
  return activeCell ? filtered.filter(r => r.analysis_map_valid && cellKey(r) === activeCell) : filtered;
}
function renderTable() {
  const selected = tableRoutes();
  $('tableHeading').textContent = activeCell ? 'Most recorded routes in the selected cell' : 'Most recorded routes in this selection';
  const top = [...selected].sort((a,b) => b.ticks-a.ticks).slice(0,tableLimit);
  $('routeRows').innerHTML = top.length ? top.map(r => `<tr><td><button class="routeinspect" data-id="${r.mp_route_id}" aria-label="Inspect ${escapeHtml(r.route_name)}">${escapeHtml(r.route_name || 'Unnamed route')}</button></td><td>${escapeHtml(r.state)}</td><td><span class="stylebadge" style="--badge:${colors[r.analysis_type]}">${r.analysis_type}</span></td><td><strong>${escapeHtml(r.analysis_grade_family || 'Unresolved')}</strong></td><td>${fmt(r.ticks)}</td><td>${fmt(r.climbers)}</td><td>${r.length_feet == null ? '—' : fmt(r.length_feet)}</td><td>${r.pitches == null ? '—' : fmt(r.pitches)}</td><td><a class="mplink" href="${escapeHtml(r.route_url)}" aria-label="Open ${escapeHtml(r.route_name)} on Mountain Project" target="_blank" rel="noopener">Mountain Project ↗</a></td></tr>`).join('') : '<tr><td colspan="9">No routes match. Try clearing grades or resetting filters.</td></tr>';
  $('tableCount').textContent = `Showing ${fmt(top.length)} of ${fmt(selected.length)} routes`;
  $('loadMore').hidden = top.length >= selected.length;
  $('remainingRoutes').textContent = selected.length > top.length ? `${fmt(selected.length-top.length)} more routes available` : 'All matching routes shown';
  $('routeRows').querySelectorAll('.routeinspect').forEach(button => button.addEventListener('click', () => {
    $('selection').innerHTML = routeDetail(routeById.get(button.dataset.id));
    $('selection').scrollIntoView({behavior:'smooth',block:'center'});
  }));
}
function updateHeadline(population) {
  $('routeCount').textContent=fmt(population.length);
  $('tickCount').textContent=fmt(population.reduce((n,r)=>n+r.ticks,0));
  $('stateCount').textContent=new Set(population.map(r=>r.state)).size;
}
function refresh(fit=false) {
  filtered=routes.filter(matching); activeCell=null; tableLimit=25; $('clearCell').hidden=true; $('selection').textContent='';
  const total=filtered.reduce((n,r)=>n+r.ticks,0);
  updateHeadline(filtered);
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
  const shown=pca.points.filter(r=>Math.abs(r.pc1)<=4.5&&Math.abs(r.pc2)<=4.5);
  for(const r of shown) {
    const color=$('pcaColor').value==='style' ? colors[r.analysis_type] : tickBand(r.ticks).color;
    svg+=`<circle class="point" data-id="${r.mp_route_id}" cx="${x(r.pc1)}" cy="${y(r.pc2)}" r="3" fill="${color}" opacity=".82" tabindex="0" role="button" aria-label="Inspect ${escapeHtml(r.route_name)}"><title>${escapeHtml(r.route_name)} · ${r.analysis_type} · ${fmt(r.ticks)} sample ticks</title></circle>`;
  }
  const names={log_length:'Log length',log_pitches:'Log pitches',grade_order:'YDS family',average_stars:'Kaggle stars',is_pg13:'PG-13 recorded',is_r:'R recorded',is_x:'X recorded'};
  const labelPositions={log_length:[2.85,.05],log_pitches:[2.85,-1.25],grade_order:[.3,2.95],average_stars:[1.55,2.25],is_pg13:[-2.8,-1.3],is_r:[-1.7,-2.05],is_x:[.25,-2.55]};
  pca.loadings.forEach(a=>{const pos=labelPositions[a.feature];svg+=`<line x1="${x(0)}" y1="${y(0)}" x2="${x(a.PC1*3)}" y2="${y(a.PC2*3)}" stroke="#24453b" stroke-width="1.5" marker-end="url(#arrow)"/><line x1="${x(a.PC1*3)}" y1="${y(a.PC2*3)}" x2="${x(pos[0])}" y2="${y(pos[1])}" stroke="#71847d" stroke-dasharray="2 3"/><text x="${x(pos[0])}" y="${y(pos[1])}" font-size="11" fill="#24453b" stroke="white" stroke-width="3" paint-order="stroke">${names[a.feature]}</text>`;});
  svg+=`<text x="${width/2}" y="${height-12}" text-anchor="middle" fill="#66747c">PC1 · unit-SD scores (${(ratio[0]*100).toFixed(1)}% variance)</text><text transform="translate(18 ${height/2}) rotate(-90)" text-anchor="middle" fill="#66747c">PC2 · unit-SD scores (${(ratio[1]*100).toFixed(1)}% variance)</text>`;
  $('pcaPlot').innerHTML=svg;
  $('pcaLegend').innerHTML=$('pcaColor').value==='style' ? ['Sport','Trad'].map(k=>`<span class="chip" style="background:${colors[k]}"></span>${k} &nbsp; `).join('') : tickBands.map(b=>`<span class="legendband"><span class="chip" style="background:${b.color}"></span>${b.label}</span>`).join('') + ' · sample ticks per route'; 
  $('pcaCaption').textContent=`Fit: ${fmt(pca.metadata.fit_routes)} complete sport/trad routes. Plot: ${fmt(shown.length)} visible points from a fixed ${fmt(pca.points.length)}-route sample; some scores lie outside ±4.5. PC1 + PC2 preserve ${((ratio[0]+ratio[1])*100).toFixed(1)}% of feature variance. Arrows ×3.`;
  const inspect = node => {
    const point=pca.points.find(r=>r.mp_route_id===node.dataset.id);
    const route=routeById.get(point.mp_route_id);
    $('pcaDetail').innerHTML=routeDetail(route) + `<p class="note">PC1 ${point.pc1.toFixed(2)} · PC2 ${point.pc2.toFixed(2)}</p>`;
    $('pcaPlot').querySelectorAll('.selectedpoint').forEach(n=>n.classList.remove('selectedpoint'));
    node.classList.add('selectedpoint');
  };
  $('pcaPlot').querySelectorAll('.point').forEach(node=>{
    node.addEventListener('click',()=>inspect(node));
    node.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();inspect(node);}});
  });
}

const tickBands = [
  {max:4,label:'1–4',color:'#4055a8'}, {max:9,label:'5–9',color:'#1385a1'},
  {max:24,label:'10–24',color:'#23814a'}, {max:99,label:'25–99',color:'#d17414'},
  {max:Infinity,label:'100+',color:'#bd2754'}
];
function tickBand(ticks) { return tickBands.find(b=>ticks<=b.max); }
async function renderGallery() {
  try {
    const response=await fetch('gallery.json');
    if(!response.ok) throw new Error('The report figures could not load. Please reload.');
    const gallery=await response.json();
    $('figureGallery').innerHTML=gallery.map(item=>`<article class="figurecard ${item.wide ? 'wide' : ''}"><div class="eyebrow">${escapeHtml(item.label)}</div><h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(item.description)}</p>${item.image ? `<a href="${escapeHtml(item.image)}" target="_blank" rel="noopener" aria-label="Open full-size ${escapeHtml(item.title)}"><img loading="lazy" src="${escapeHtml(item.image)}" alt="${escapeHtml(item.alt)}"></a><a class="figureopen" href="${escapeHtml(item.image)}" target="_blank" rel="noopener">Open full-size figure ↗</a>` : ''}${item.rows ? `<div class="scroll"><table><thead><tr>${item.headers.map(h=>`<th>${escapeHtml(h)}</th>`).join('')}</tr></thead><tbody>${item.rows.map(row=>`<tr>${row.map(cell=>`<td>${escapeHtml(cell)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>` : ''}<p class="figurecaption">${escapeHtml(item.caption || item.description)}</p></article>`).join('');
  } catch(error) { $('figureGallery').textContent=error.message; }
}

document.querySelectorAll('nav button').forEach(button=>button.addEventListener('click',()=>{
  document.querySelectorAll('.page').forEach(page=>page.hidden=page.id!==button.dataset.page);
  document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b===button));
  updateHeadline(button.dataset.page==='atlas' ? filtered : routes);
  if(button.dataset.page==='atlas'&&map) map.invalidateSize(); if(button.dataset.page==='pca') pcaDraw();
}));
async function init() {
  if(typeof L==='undefined') throw new Error('The map library could not load. Check your internet connection and reload.');
  const responses=await Promise.all([fetch('data/routes.json'),fetch('data/pca.json')]);
  if(responses.some(r=>!r.ok)) throw new Error('Route exports are missing. Run python scripts/eda.py, then serve the web directory.');
  const [payload,projection]=await Promise.all(responses.map(r=>r.json()));
  routes=unpack(payload); routeById=new Map(routes.map(r=>[r.mp_route_id,r])); pca={...projection,points:unpack(projection)};
  [...new Set(routes.map(r=>r.state))].sort().forEach(state=>$('state').add(new Option(state,state)));
  map=L.map('map',{preferCanvas:true,scrollWheelZoom:false}).setView([39,-98],4);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'}).addTo(map);
  layers=L.layerGroup().addTo(map); L.control.scale().addTo(map);
  for(const id of ['type','state','metric','risk','length']) $(id).addEventListener('change',()=>{if(id==='type'||id==='state') updateGrades();refresh(id==='state');});
  let timer; $('search').addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(()=>refresh(),160);});
  $('reset').addEventListener('click',()=>{['type','state','risk','length'].forEach(id=>$(id).value='all');$('metric').value='ticks';$('search').value='';$('cellSize').value='0.2';CELL=.2;selectedGrades.clear();updateGrades();refresh();map.setView([39,-98],4);});
  $('cellSize').addEventListener('change',()=>{CELL=Number($('cellSize').value);refresh();});
  $('gradeScale').addEventListener('change',updateRangeOptions);
  $('allGrades').addEventListener('click',()=>{selectedGrades.clear();updateGradeSummary();refresh();});
  $('applyRange').addEventListener('click',()=>{
    const grades=availableGrades.filter(([g])=>$('gradeScale').value==='yds'?g.startsWith('5.'):g.startsWith('V')).map(([g])=>g);
    const first=grades.indexOf($('gradeFrom').value), last=grades.indexOf($('gradeTo').value);
    selectedGrades.clear();
    grades.slice(Math.min(first,last),Math.max(first,last)+1).forEach(g=>selectedGrades.add(g));
    updateGradeSummary();refresh(); document.querySelector('.gradepicker').open=false;
  });
  $('loadMore').addEventListener('click',()=>{tableLimit+=25;renderTable();});
  $('fit').addEventListener('click',fitRoutes);
  $('clearCell').addEventListener('click',()=>{activeCell=null;tableLimit=25;$('clearCell').hidden=true;$('selection').textContent='';renderTable();});
  $('pcaColor').addEventListener('change',pcaDraw);
  $('download').addEventListener('click',()=>{
    const columns=['mp_route_id','route_name','state','analysis_type','analysis_grade_family','rating_raw','ticks','climbers','length_feet','pitches','protection_group','average_stars','historical_average_user_rating','rating_valid_count','route_url'];
    const csv=[columns.join(','),...filtered.map(r=>columns.map(c=>'"'+String(r[c]??'').replaceAll('"','""')+'"').join(','))].join('\n');
    const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='climbing_filtered_sample.csv';a.click();URL.revokeObjectURL(url);
  });
  renderGallery(); updateGrades();refresh();$('loadStatus').textContent=`Loaded ${fmt(routes.length)} core rock routes. Default map view shows the contiguous U.S.; Alaska and Hawaii are included and available through the state filter. The full sample represents 48 of 50 states: Louisiana and Nebraska have no retained routes, which does not mean there is no climbing there.`;
}
init().catch(error=>{$('loadStatus').textContent=error.message;console.error(error);});
