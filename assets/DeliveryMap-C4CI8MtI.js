import{_ as e,n as t,r as n,y as r}from"./cn-WLc0uQTC.js";import{a as i,i as a,l as o,n as s,o as c,r as l,t as u}from"./TileLayer-Ji879LPu.js";import{t as d}from"./Polyline-HIb5fqg6.js";/* empty css                */var f=t(`arrow-left`,[[`path`,{d:`m12 19-7-7 7-7`,key:`1l729n`}],[`path`,{d:`M19 12H5`,key:`x3x0zl`}]]),p=r(e(),1),m=r(o(),1),h=n(),g=[48.8566,2.3522],_=e=>`
	<div class="dm-pin-wrap">
		<svg width="34" height="44" viewBox="0 0 34 44" xmlns="http://www.w3.org/2000/svg">
			<defs>
				<filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
					<feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="rgba(15,23,42,0.35)"/>
				</filter>
			</defs>
			<path filter="url(#shadow)" d="M17 0C7.6 0 0 7.6 0 17c0 12.4 17 27 17 27s17-14.6 17-27C34 7.6 26.4 0 17 0z" fill="${e}"/>
			<circle cx="17" cy="17" r="7" fill="white"/>
		</svg>
	</div>
`,v=e=>m.default.divIcon({className:`delivery-map-marker`,html:_(e),iconSize:[34,44],iconAnchor:[17,44],popupAnchor:[0,-40]}),y=`#3b82f6`,b=`#ef4444`,x=(e,t)=>{if(!e||!t)return 0;let n=e=>e*Math.PI/180,r=n(t[0]-e[0]),i=n(t[1]-e[1]),a=n(e[0]),o=n(t[0]),s=Math.sin(r/2)**2+Math.sin(i/2)**2*Math.cos(a)*Math.cos(o);return Math.round(2*6371*Math.asin(Math.sqrt(s))*10)/10},S=async(e,t,n)=>{if(!e||!t)return{positions:[],distanceKm:0};let[r,i]=e,[a,o]=t,s=`https://router.project-osrm.org/route/v1/driving/${i},${r};${o},${a}?overview=full&geometries=geojson`,c=await fetch(s,{signal:n,headers:{Accept:`application/json`}});if(!c.ok)throw Error(`Routing request failed`);let l=await c.json();if(l?.code!==`Ok`||!Array.isArray(l?.routes)||l.routes.length===0)throw Error(`No route found`);let u=l.routes[0];return{positions:Array.isArray(u?.geometry?.coordinates)?u.geometry.coordinates.map(([e,t])=>[t,e]):[],distanceKm:Math.round((u.distance??0)/1e3*10)/10}},C=async(e,t)=>{if(!e||e.trim().length<2)return[];let n=`https://nominatim.openstreetmap.org/search?format=json&addressdetails=1&limit=5&q=${encodeURIComponent(e)}`,r=await fetch(n,{signal:t,headers:{Accept:`application/json`}});return r.ok?(await r.json()).map(e=>({label:e.display_name,latitude:parseFloat(e.lat),longitude:parseFloat(e.lon)})):[]},w=async(e,t,n)=>{try{let r=`https://nominatim.openstreetmap.org/reverse?format=json&lat=${e}&lon=${t}`,i=await fetch(r,{signal:n,headers:{Accept:`application/json`}});return i.ok?(await i.json())?.display_name??null:null}catch{return null}},T=({points:e})=>{let t=i();return(0,p.useEffect)(()=>{e.length===2?t.fitBounds(e,{padding:[60,60]}):e.length===1&&t.setView(e[0],14)},[t,e]),null},E=()=>{let e=i();return(0,p.useEffect)(()=>{e.invalidateSize()},[e]),null},D=({mode:e,onPickLocation:t,clickCount:n,setClickCount:r})=>(c({click(i){if(e!==`create`||!t)return;let{lat:a,lng:o}=i.latlng;if(n===0){t({type:`pickup`,latitude:a,longitude:o}),r(1);return}t({type:`dropoff`,latitude:a,longitude:o}),r(2)}}),null),O=({label:e,color:t,placeholder:n,onSelect:r})=>{let[i,a]=(0,p.useState)(``),[o,s]=(0,p.useState)([]),[c,l]=(0,p.useState)(!1),[u,d]=(0,p.useState)(!1),f=(0,p.useRef)(null),m=(0,p.useRef)(null);(0,p.useEffect)(()=>{if(m.current&&clearTimeout(m.current),!i||i.trim().length<2){s([]);return}return m.current=setTimeout(async()=>{f.current&&f.current.abort();let e=new AbortController;f.current=e,l(!0);try{let t=await C(i,e.signal);s(t),d(!0)}catch(e){e.name!==`AbortError`&&s([])}finally{l(!1)}},400),()=>clearTimeout(m.current)},[i]);let g=e=>{a(e.label),d(!1),s([]),r(e)};return(0,h.jsxs)(`div`,{className:`dm-search-field`,children:[(0,h.jsx)(`span`,{className:`dm-search-dot`,style:{background:t}}),(0,h.jsx)(`input`,{type:`text`,value:i,placeholder:n,onChange:e=>a(e.target.value),onFocus:()=>o.length>0&&d(!0),onBlur:()=>setTimeout(()=>d(!1),150),className:`dm-search-input`}),c?(0,h.jsx)(`span`,{className:`dm-search-spinner`}):null,u&&o.length>0?(0,h.jsx)(`ul`,{className:`dm-suggestions`,children:o.map((e,t)=>(0,h.jsx)(`li`,{onMouseDown:()=>g(e),className:`dm-suggestion-item`,children:e.label},t))}):null,(0,h.jsx)(`div`,{className:`dm-search-label`,children:e})]})},k=({mode:e=`view`,pickup:t,dropoff:n,onPickLocation:r,height:i=`clamp(320px, 55vh, 560px)`,className:o=``,showSearch:c=!0})=>{let[f,m]=(0,p.useState)(0),[_,C]=(0,p.useState)([]),[k,A]=(0,p.useState)(0),[j,M]=(0,p.useState)(!1),[N,P]=(0,p.useState)(`haversine`),F=(0,p.useMemo)(()=>t?.latitude===null||t?.longitude===null||t?.latitude===void 0||t?.longitude===void 0?null:[Number(t.latitude),Number(t.longitude)],[t?.latitude,t?.longitude]),I=(0,p.useMemo)(()=>n?.latitude===null||n?.longitude===null||n?.latitude===void 0||n?.longitude===void 0?null:[Number(n.latitude),Number(n.longitude)],[n?.latitude,n?.longitude]);(0,p.useEffect)(()=>{e===`create`&&m(+!!F)},[e,F]);let L=(0,p.useMemo)(()=>[F,I].filter(Boolean),[F,I]),R=x(F,I),z=k||R,B=!!r;(0,p.useEffect)(()=>{if(!F||!I){C([]),A(0),M(!1),P(`haversine`);return}let e=new AbortController;return M(!0),(async()=>{try{let t=await S(F,I,e.signal);C(t.positions),A(t.distanceKm),P(`route`)}catch(e){if(e.name===`AbortError`)return;C([F,I]),A(R),P(`haversine`)}finally{e.signal.aborted||M(!1)}})(),()=>e.abort()},[F,I,R]);let V=(0,p.useCallback)(e=>t=>{r?.({type:e,latitude:t.latitude,longitude:t.longitude,label:t.label})},[r]),H=(0,p.useCallback)(e=>async t=>{let{lat:n,lng:i}=t.target.getLatLng();r?.({type:e,latitude:n,longitude:i});let a=await w(n,i);a&&r?.({type:e,latitude:n,longitude:i,label:a})},[r]);return(0,h.jsxs)(`div`,{className:`delivery-map-shell ${o}`,style:{height:typeof i==`number`?`${i}px`:i},children:[(0,h.jsx)(`style`,{children:`
				.delivery-map-shell {
					position: relative;
					width: 100%;
					border-radius: var(--r-xl);
					overflow: hidden;
					box-shadow: var(--shadow-xs);
					border: 1px solid var(--border);
					background: var(--bg-subtle);
					font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
				}
				.delivery-map { width: 100%; height: 100%; z-index: 0; min-height: 200px; }

				.dm-pin-wrap { filter: drop-shadow(0 1px 1px rgba(0,0,0,0.15)); }
				.delivery-map-marker { background: transparent; border: none; }

				/* Barre de recherche flottante */
				.dm-search-bar {
					position: absolute;
					top: 14px;
					left: 14px;
					right: 14px;
					z-index: 500;
					display: flex;
					gap: 10px;
					align-items: center;
					background: rgba(255, 255, 255, 0.85);
					backdrop-filter: blur(12px) saturate(180%);
					-webkit-backdrop-filter: blur(12px) saturate(180%);
					border-radius: 16px;
					padding: 10px 12px;
					box-shadow: 0 8px 24px rgba(15, 23, 42, 0.15);
					border: 1px solid rgba(255, 255, 255, 0.6);
				}
				.dm-search-field {
					position: relative;
					flex: 1;
					display: flex;
					align-items: center;
					gap: 8px;
					background: #fff;
					border-radius: 12px;
					padding: 8px 12px;
					border: 1px solid rgba(148, 163, 184, 0.35);
					transition: border-color 0.15s ease, box-shadow 0.15s ease;
				}
				.dm-search-field:focus-within {
					border-color: #6366f1;
					box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
				}
				.dm-search-dot {
					width: 9px;
					height: 9px;
					border-radius: 50%;
					flex-shrink: 0;
					box-shadow: 0 0 0 3px rgba(0,0,0,0.05);
				}
				.dm-search-input {
					border: none;
					outline: none;
					flex: 1;
					font-size: 13.5px;
					color: #0f172a;
					background: transparent;
					min-width: 0;
				}
				.dm-search-input::placeholder { color: #94a3b8; }
				.dm-search-label {
					position: absolute;
					top: -9px;
					left: 10px;
					font-size: 10px;
					font-weight: 600;
					letter-spacing: 0.04em;
					text-transform: uppercase;
					color: #64748b;
					background: #fff;
					padding: 0 6px;
					border-radius: 6px;
				}
				.dm-search-spinner {
					width: 14px;
					height: 14px;
					border-radius: 50%;
					border: 2px solid rgba(99,102,241,0.25);
					border-top-color: #6366f1;
					animation: dm-spin 0.7s linear infinite;
					flex-shrink: 0;
				}
				@keyframes dm-spin { to { transform: rotate(360deg); } }

				.dm-suggestions {
					position: absolute;
					top: calc(100% + 6px);
					left: 0;
					right: 0;
					background: #fff;
					border-radius: 12px;
					box-shadow: 0 12px 28px rgba(15, 23, 42, 0.18);
					border: 1px solid rgba(148, 163, 184, 0.25);
					list-style: none;
					margin: 0;
					padding: 6px;
					max-height: 220px;
					overflow-y: auto;
					z-index: 600;
				}
				.dm-suggestion-item {
					padding: 8px 10px;
					font-size: 12.5px;
					color: #334155;
					border-radius: 8px;
					cursor: pointer;
					line-height: 1.35;
				}
				.dm-suggestion-item:hover { background: #f1f5f9; color: #0f172a; }

				.dm-swap-btn {
					flex-shrink: 0;
					width: 34px;
					height: 34px;
					border-radius: 10px;
					border: 1px solid rgba(148, 163, 184, 0.35);
					background: #fff;
					display: flex;
					align-items: center;
					justify-content: center;
					cursor: pointer;
					color: #475569;
					transition: transform 0.15s ease, background 0.15s ease;
				}
				.dm-swap-btn:hover { background: #f8fafc; transform: rotate(180deg); }

				/* Footer info */
				.delivery-map-meta {
					position: absolute;
					bottom: 14px;
					left: 14px;
					z-index: 500;
					display: flex;
					gap: 10px;
					background: rgba(255, 255, 255, 0.85);
					backdrop-filter: blur(12px) saturate(180%);
					-webkit-backdrop-filter: blur(12px) saturate(180%);
					border-radius: 14px;
					padding: 8px 14px;
					box-shadow: 0 8px 24px rgba(15, 23, 42, 0.15);
					border: 1px solid rgba(255, 255, 255, 0.6);
				}
				.delivery-map-meta > div {
					display: flex;
					flex-direction: column;
					padding-right: 12px;
					border-right: 1px solid rgba(148,163,184,0.3);
				}
				.delivery-map-meta > div:last-child { border-right: none; padding-right: 0; }
				.delivery-map-meta strong {
					font-size: 10px;
					text-transform: uppercase;
					letter-spacing: 0.04em;
					color: #64748b;
					font-weight: 600;
				}
				.delivery-map-meta span {
					font-size: 13.5px;
					font-weight: 600;
					color: #0f172a;
				}

				.dm-hint {
					position: absolute;
					bottom: 14px;
					right: 14px;
					z-index: 500;
					background: rgba(15, 23, 42, 0.75);
					color: #fff;
					font-size: 11px;
					padding: 6px 10px;
					border-radius: 10px;
					backdrop-filter: blur(6px);
					max-width: 60%;
					text-align: right;
				}

				/* -------------------------------------------------------------- */
				/* Responsive - tablette (≤ 768px)                                 */
				/* -------------------------------------------------------------- */
				@media (max-width: 768px) {
					.delivery-map-shell { border-radius: 14px; }
					.dm-search-bar { top: 10px; left: 10px; right: 10px; padding: 8px; border-radius: 14px; }
					.dm-search-field { padding: 7px 10px; }
					.dm-search-input { font-size: 13px; }
					.delivery-map-meta { bottom: 10px; left: 10px; padding: 7px 12px; }
				}

				/* -------------------------------------------------------------- */
				/* Responsive - mobile (≤ 560px)                                   */
				/* -------------------------------------------------------------- */
				@media (max-width: 560px) {
					.delivery-map-shell { border-radius: 12px; }

					/* La barre de recherche passe en colonne, avec le bouton swap au centre */
					.dm-search-bar {
						flex-direction: column;
						align-items: stretch;
						gap: 6px;
						padding: 8px;
						border-radius: 16px;
					}
					.dm-search-field { width: 100%; padding: 9px 10px; }
					.dm-search-label { font-size: 9px; top: -8px; }
					.dm-suggestions { max-height: 160px; font-size: 12px; }
					.dm-suggestion-item { font-size: 12px; padding: 7px 9px; }

					.dm-swap-btn {
						align-self: center;
						width: 30px;
						height: 30px;
						transform: rotate(90deg);
						font-size: 13px;
					}
					.dm-swap-btn:hover { transform: rotate(270deg); }

					/* Le panneau meta passe en pleine largeur au-dessus du bord inférieur */
					.delivery-map-meta {
						left: 10px;
						right: 10px;
						bottom: 10px;
						justify-content: space-between;
						padding: 7px 10px;
						border-radius: 12px;
					}
					.delivery-map-meta > div { padding-right: 8px; }
					.delivery-map-meta strong { font-size: 9px; }
					.delivery-map-meta span { font-size: 12px; }

					/* Le hint passe au-dessus de la barre meta pour ne pas se chevaucher */
					.dm-hint {
						left: 10px;
						right: 10px;
						bottom: 58px;
						max-width: none;
						text-align: center;
						font-size: 10.5px;
						padding: 5px 10px;
					}

					/* Pins légèrement réduits pour laisser plus de place à la carte */
					.delivery-map-marker { transform: scale(0.85); transform-origin: bottom center; }
				}

				/* -------------------------------------------------------------- */
				/* Responsive - très petit écran (≤ 380px)                         */
				/* -------------------------------------------------------------- */
				@media (max-width: 380px) {
					.dm-search-input { font-size: 12px; }
					.dm-search-dot { width: 7px; height: 7px; }
					.delivery-map-meta { flex-direction: row; }
					.delivery-map-meta strong { display: none; }
				}
			`}),c?(0,h.jsxs)(`div`,{className:`dm-search-bar`,children:[(0,h.jsx)(O,{label:`Départ`,color:y,placeholder:`Rechercher une ville ou adresse de départ...`,onSelect:V(`pickup`)}),(0,h.jsx)(`button`,{type:`button`,className:`dm-swap-btn`,onClick:()=>{!r||!F||!I||(r({type:`pickup`,latitude:I[0],longitude:I[1],label:n?.label}),r({type:`dropoff`,latitude:F[0],longitude:F[1],label:t?.label}))},title:`Inverser départ / arrivée`,children:`⇄`}),(0,h.jsx)(O,{label:`Arrivée`,color:b,placeholder:`Rechercher une ville ou adresse d'arrivée...`,onSelect:V(`dropoff`)})]}):null,(0,h.jsxs)(a,{zoomControl:!1,center:g,zoom:12,className:`delivery-map`,children:[(0,h.jsx)(E,{}),(0,h.jsx)(D,{mode:e,onPickLocation:r,clickCount:f,setClickCount:m}),(0,h.jsx)(u,{url:`https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png`,attribution:`© OpenStreetMap contributors`}),(0,h.jsx)(T,{points:L}),F?(0,h.jsx)(l,{position:F,icon:v(y),draggable:B,eventHandlers:B?{dragend:H(`pickup`)}:void 0,children:(0,h.jsxs)(s,{children:[(0,h.jsx)(`strong`,{children:`Pickup`}),(0,h.jsx)(`br`,{}),t?.label||`${F[0].toFixed(5)}, ${F[1].toFixed(5)}`,B?(0,h.jsx)(`div`,{style:{marginTop:4,fontSize:11,color:`#64748b`},children:`Glissez pour déplacer`}):null]})}):null,I?(0,h.jsx)(l,{position:I,icon:v(b),draggable:B,eventHandlers:B?{dragend:H(`dropoff`)}:void 0,children:(0,h.jsxs)(s,{children:[(0,h.jsx)(`strong`,{children:`Dropoff`}),(0,h.jsx)(`br`,{}),n?.label||`${I[0].toFixed(5)}, ${I[1].toFixed(5)}`,B?(0,h.jsx)(`div`,{style:{marginTop:4,fontSize:11,color:`#64748b`},children:`Glissez pour déplacer`}):null]})}):null,F&&I?(0,h.jsx)(d,{positions:_.length>1?_:[F,I],pathOptions:{color:`#6366f1`,weight:4,opacity:.9,lineCap:`round`}}):null]}),(0,h.jsxs)(`div`,{className:`delivery-map-meta`,children:[(0,h.jsxs)(`div`,{children:[(0,h.jsx)(`strong`,{children:`Distance`}),(0,h.jsx)(`span`,{children:j?`Calcul...`:z?`${z} km`:`N/A`})]}),(0,h.jsxs)(`div`,{children:[(0,h.jsx)(`strong`,{children:`Source`}),(0,h.jsx)(`span`,{children:N===`route`?`Route OSM`:`Estimation`})]}),(0,h.jsxs)(`div`,{children:[(0,h.jsx)(`strong`,{children:`Mode`}),(0,h.jsx)(`span`,{children:e===`create`?`Creation`:`Visualisation`})]})]}),e===`create`&&B?(0,h.jsx)(`div`,{className:`dm-hint`,children:f===0?`Cliquez pour placer le départ`:f===1?`Cliquez pour placer l'arrivée`:`Glissez les points pour ajuster`}):null]})};export{f as n,k as t};