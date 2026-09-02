import{_ as e,r as t,y as n}from"./cn-WLc0uQTC.js";import{a as r,i,l as a,n as o,r as s,t as c}from"./TileLayer-Ji879LPu.js";/* empty css                */var l=n(e(),1),u=n(a(),1),d=t(),f=[48.8566,2.3522],p=({color:e=`#2563eb`,selected:t=!1,heading:n=0})=>{let r=t?40:34,i=t?`<div class="vtm-pulse" style="--vtm-color:${e}"></div>`:``;return u.default.divIcon({className:`vtm-marker`,html:`
			<div class="vtm-marker-inner" style="width:${r}px;height:${r}px;">
				${i}
				<div class="vtm-dot" style="background:${e};transform:rotate(${n}deg);">
					<svg viewBox="0 0 24 24" width="${t?20:17}" height="${t?20:17}" fill="none" xmlns="http://www.w3.org/2000/svg">
						<path d="M12 2 L19 20 L12 16.5 L5 20 Z" fill="white"/>
					</svg>
				</div>
			</div>
		`,iconSize:[r,r],iconAnchor:[r/2,r/2],popupAnchor:[0,-r/2]})},m=u.default.divIcon({className:`vtm-search-marker`,html:`
		<div class="vtm-search-pin">
			<svg viewBox="0 0 24 32" width="34" height="44" xmlns="http://www.w3.org/2000/svg">
				<path d="M12 0C5.4 0 0 5.4 0 12c0 9 12 20 12 20s12-11 12-20c0-6.6-5.4-12-12-12z" fill="#9333ea"/>
				<circle cx="12" cy="12" r="5" fill="white"/>
			</svg>
		</div>
	`,iconSize:[34,44],iconAnchor:[17,44],popupAnchor:[0,-40]}),h=({locations:e,selectedVehicleId:t})=>{let n=r(),i=(0,l.useRef)(!1),a=(0,l.useRef)(!1),o=(0,l.useRef)(!1),s=(0,l.useRef)(null),c=(0,l.useRef)(void 0);(0,l.useEffect)(()=>{let e=()=>{o.current||(a.current=!0)};return n.on(`dragstart`,e),n.on(`zoomstart`,e),()=>{n.off(`dragstart`,e),n.off(`zoomstart`,e)}},[n]);let d=e=>{o.current=!0,e(),setTimeout(()=>{o.current=!1},0)};return(0,l.useEffect)(()=>{if(e.length===0)return;let r=e.map(e=>e.vehicleId).sort().join(`,`),o=r!==s.current,l=t!==c.current;if(s.current=r,c.current=t,l&&t&&(a.current=!1),!(!i.current||l||o&&!a.current))return;let f=e.find(e=>String(e.vehicleId)===String(t));d(()=>{if(f)n.setView([f.latitude,f.longitude],Math.max(n.getZoom(),15),{animate:i.current});else if(e.length===1)n.setView([e[0].latitude,e[0].longitude],15,{animate:i.current});else{let t=u.default.latLngBounds(e.map(e=>[e.latitude,e.longitude]));n.fitBounds(t,{padding:[56,56],maxZoom:15,animate:i.current})}}),i.current=!0},[n,e,t]),null},g=()=>{let e=r(),[t,n]=(0,l.useState)(!1),[i,a]=(0,l.useState)(``),[c,f]=(0,l.useState)([]),[p,h]=(0,l.useState)(!1),[g,_]=(0,l.useState)(!1),[v,y]=(0,l.useState)(null),b=(0,l.useRef)(null),x=(0,l.useRef)(null);(0,l.useEffect)(()=>{if(!i||i.trim().length<3){f([]),h(!1);return}let e=new AbortController;h(!0);let t=setTimeout(async()=>{try{let t=`https://nominatim.openstreetmap.org/search?format=json&addressdetails=1&limit=6&q=${encodeURIComponent(i)}`,n=await(await fetch(t,{signal:e.signal,headers:{"Accept-Language":`fr`}})).json();f(Array.isArray(n)?n:[])}catch(e){e.name!==`AbortError`&&f([])}finally{h(!1)}},400);return()=>{clearTimeout(t),e.abort()}},[i]);let S=()=>{n(!0),setTimeout(()=>b.current?.focus(),50)},C=()=>{n(!1),_(!1),a(``),f([]),y(null)},w=()=>{a(``),f([]),b.current?.focus()},T=t=>{let n=parseFloat(t.lat),r=parseFloat(t.lon);if(!(Number.isNaN(n)||Number.isNaN(r)))if(y({lat:n,lon:r,label:t.display_name}),a(t.display_name),f([]),_(!1),b.current?.blur(),t.boundingbox&&t.boundingbox.length===4){let[n,r,i,a]=t.boundingbox.map(Number),o=u.default.latLngBounds([n,i],[r,a]);e.flyToBounds(o,{padding:[48,48],maxZoom:16,duration:.8})}else e.flyTo([n,r],14,{duration:.8})};return(0,l.useEffect)(()=>{_(c.length>0&&document.activeElement===b.current)},[c]),(0,d.jsxs)(d.Fragment,{children:[(0,d.jsx)(`div`,{className:`vtm-search-control ${t?`vtm-search-control--open`:``}`,children:t?(0,d.jsxs)(`div`,{className:`vtm-search-bar`,children:[(0,d.jsxs)(`svg`,{className:`vtm-search-icon`,width:`16`,height:`16`,viewBox:`0 0 24 24`,fill:`none`,xmlns:`http://www.w3.org/2000/svg`,children:[(0,d.jsx)(`circle`,{cx:`11`,cy:`11`,r:`7`,stroke:`#64748b`,strokeWidth:`2`}),(0,d.jsx)(`path`,{d:`M21 21l-4.3-4.3`,stroke:`#64748b`,strokeWidth:`2`,strokeLinecap:`round`})]}),(0,d.jsx)(`input`,{ref:b,type:`text`,value:i,placeholder:`Ville, adresse...`,className:`vtm-search-input`,onChange:e=>a(e.target.value),onFocus:()=>{x.current&&clearTimeout(x.current),c.length>0&&_(!0)},onBlur:()=>{x.current=setTimeout(()=>_(!1),150)}}),p&&(0,d.jsx)(`span`,{className:`vtm-search-spinner`,"aria-hidden":`true`}),!p&&i&&(0,d.jsx)(`button`,{type:`button`,className:`vtm-search-clear`,title:`Effacer`,onMouseDown:e=>e.preventDefault(),onClick:w,children:(0,d.jsx)(`svg`,{width:`12`,height:`12`,viewBox:`0 0 24 24`,fill:`none`,xmlns:`http://www.w3.org/2000/svg`,children:(0,d.jsx)(`path`,{d:`M6 6l12 12M18 6L6 18`,stroke:`#94a3b8`,strokeWidth:`2.4`,strokeLinecap:`round`})})}),(0,d.jsx)(`button`,{type:`button`,className:`vtm-search-close`,title:`Fermer la recherche`,onMouseDown:e=>e.preventDefault(),onClick:C,children:(0,d.jsx)(`svg`,{width:`14`,height:`14`,viewBox:`0 0 24 24`,fill:`none`,xmlns:`http://www.w3.org/2000/svg`,children:(0,d.jsx)(`path`,{d:`M6 6l12 12M18 6L6 18`,stroke:`#0f172a`,strokeWidth:`2.4`,strokeLinecap:`round`})})}),g&&c.length>0&&(0,d.jsx)(`ul`,{className:`vtm-search-suggestions`,children:c.map(e=>(0,d.jsx)(`li`,{children:(0,d.jsxs)(`button`,{type:`button`,className:`vtm-search-suggestion`,onMouseDown:e=>e.preventDefault(),onClick:()=>T(e),children:[(0,d.jsx)(`svg`,{width:`14`,height:`14`,viewBox:`0 0 24 24`,fill:`none`,xmlns:`http://www.w3.org/2000/svg`,className:`vtm-search-suggestion-pin`,children:(0,d.jsx)(`path`,{d:`M12 0C5.4 0 0 5.4 0 12c0 9 12 20 12 20s12-11 12-20c0-6.6-5.4-12-12-12z`,transform:`scale(0.58) translate(0,0)`,fill:`#9333ea`})}),(0,d.jsxs)(`span`,{className:`vtm-search-suggestion-text`,children:[(0,d.jsx)(`span`,{className:`vtm-search-suggestion-main`,children:e.display_name.split(`,`)[0]}),(0,d.jsx)(`span`,{className:`vtm-search-suggestion-sub`,children:e.display_name.split(`,`).slice(1).join(`,`).trim()})]})]})},e.place_id))})]}):(0,d.jsx)(`button`,{type:`button`,className:`vtm-search-toggle`,title:`Rechercher une ville ou une adresse`,onClick:S,children:(0,d.jsxs)(`svg`,{width:`18`,height:`18`,viewBox:`0 0 24 24`,fill:`none`,xmlns:`http://www.w3.org/2000/svg`,children:[(0,d.jsx)(`circle`,{cx:`11`,cy:`11`,r:`7`,stroke:`#0f172a`,strokeWidth:`2`}),(0,d.jsx)(`path`,{d:`M21 21l-4.3-4.3`,stroke:`#0f172a`,strokeWidth:`2`,strokeLinecap:`round`})]})})}),v&&(0,d.jsx)(s,{position:[v.lat,v.lon],icon:m,children:(0,d.jsxs)(o,{children:[(0,d.jsx)(`div`,{className:`vtm-popup-title`,children:`Résultat de recherche`}),(0,d.jsxs)(`div`,{className:`vtm-popup-row`,children:[`📍 `,v.label]})]})})]})},_=e=>{if(!e)return`Inconnue`;let t=Date.now()-new Date(e).getTime(),n=Math.round(t/6e4);if(n<1)return`À l'instant`;if(n<60)return`Il y a ${n} min`;let r=Math.round(n/60);return r<24?`Il y a ${r} h`:new Date(e).toLocaleDateString(`fr-FR`)},v=({locations:e=[],selectedVehicleId:t=null,vehiclesById:n={},color:r=`#2563eb`,height:a=420})=>{let[u,m]=(0,l.useState)(0),[v,y]=(0,l.useState)(!1),b=(0,l.useRef)(null),x=(0,l.useMemo)(()=>{let t=e[0];return t?[t.latitude,t.longitude]:f},[]);return(0,l.useEffect)(()=>{let e=()=>{y(document.fullscreenElement===b.current)};return document.addEventListener(`fullscreenchange`,e),()=>document.removeEventListener(`fullscreenchange`,e)},[]),(0,d.jsxs)(`div`,{ref:b,className:`tracking-map-shell ${v?`tracking-map-shell--fullscreen`:``}`,style:{height:v?`100%`:typeof a==`number`?`${a}px`:a},children:[(0,d.jsx)(`style`,{children:`
				.tracking-map-shell {
					position: relative;
					width: 100%;
					overflow: hidden;
					border-radius: var(--r-xl);
					border: 1px solid var(--border);
					box-shadow: var(--shadow-xs);
					background: var(--bg-subtle);
				}
				.vehicle-tracking-map { width: 100%; height: 100%; }

				/* Barre d'info flottante */
				.vtm-topbar {
					position: absolute;
					top: 14px;
					left: 14px;
					z-index: 500;
					display: flex;
					align-items: center;
					gap: 8px;
					padding: 8px 14px;
					border-radius: 999px;
					background: rgba(255, 255, 255, 0.85);
					backdrop-filter: blur(10px);
					box-shadow: 0 8px 20px rgba(15, 23, 42, 0.12);
					font: 600 13px/1.2 'Inter', system-ui, sans-serif;
					color: #0f172a;
				}
				.vtm-topbar .vtm-count-dot {
					width: 8px; height: 8px; border-radius: 999px; background: ${r};
					box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
				}

				.vtm-recenter-btn {
					position: absolute;
					top: 14px;
					right: 14px;
					z-index: 500;
					display: flex;
					align-items: center;
					justify-content: center;
					width: 40px;
					height: 40px;
					border-radius: 999px;
					border: none;
					background: rgba(255, 255, 255, 0.9);
					backdrop-filter: blur(10px);
					box-shadow: 0 8px 20px rgba(15, 23, 42, 0.14);
					cursor: pointer;
					transition: transform 0.15s ease, box-shadow 0.15s ease;
				}
				.vtm-recenter-btn:hover {
					transform: translateY(-1px);
					box-shadow: 0 10px 24px rgba(15, 23, 42, 0.2);
				}
				.vtm-recenter-btn:active { transform: translateY(0); }

				.vtm-fullscreen-btn {
					position: absolute;
					top: 14px;
					right: 64px;
					z-index: 500;
					display: flex;
					align-items: center;
					justify-content: center;
					width: 40px;
					height: 40px;
					border-radius: 999px;
					border: none;
					background: rgba(255, 255, 255, 0.9);
					backdrop-filter: blur(10px);
					box-shadow: 0 8px 20px rgba(15, 23, 42, 0.14);
					cursor: pointer;
					transition: transform 0.15s ease, box-shadow 0.15s ease;
				}
				.vtm-fullscreen-btn:hover {
					transform: translateY(-1px);
					box-shadow: 0 10px 24px rgba(15, 23, 42, 0.2);
				}
				.vtm-fullscreen-btn:active { transform: translateY(0); }

				.tracking-map-shell--fullscreen {
					border-radius: 0;
					width: 100vw;
					height: 100vh;
				}

				/* --- Contrôle de recherche (ville / adresse) --- */
				.vtm-search-control {
					position: absolute;
					top: 14px;
					right: 114px;
					z-index: 600;
					display: flex;
					justify-content: flex-end;
					max-width: calc(100% - 128px);
				}
				.vtm-search-control--open { max-width: min(340px, calc(100% - 128px)); }

				.vtm-search-toggle {
					display: flex;
					align-items: center;
					justify-content: center;
					width: 40px;
					height: 40px;
					flex-shrink: 0;
					border-radius: 999px;
					border: none;
					background: rgba(255, 255, 255, 0.9);
					backdrop-filter: blur(10px);
					box-shadow: 0 8px 20px rgba(15, 23, 42, 0.14);
					cursor: pointer;
					transition: transform 0.15s ease, box-shadow 0.15s ease;
				}
				.vtm-search-toggle:hover {
					transform: translateY(-1px);
					box-shadow: 0 10px 24px rgba(15, 23, 42, 0.2);
				}

				.vtm-search-bar {
					position: relative;
					display: flex;
					align-items: center;
					gap: 8px;
					width: min(340px, 100%);
					padding: 0 8px 0 12px;
					height: 40px;
					border-radius: 999px;
					background: rgba(255, 255, 255, 0.95);
					backdrop-filter: blur(10px);
					box-shadow: 0 8px 24px rgba(15, 23, 42, 0.18);
					animation: vtm-search-expand 0.18s ease-out;
				}
				@keyframes vtm-search-expand {
					from { opacity: 0; transform: scaleX(0.85); }
					to { opacity: 1; transform: scaleX(1); }
				}
				.vtm-search-bar { transform-origin: right center; }

				.vtm-search-icon { flex-shrink: 0; }

				.vtm-search-input {
					flex: 1;
					min-width: 0;
					border: none;
					outline: none;
					background: transparent;
					font: 500 13px/1.2 'Inter', system-ui, sans-serif;
					color: #0f172a;
				}
				.vtm-search-input::placeholder { color: #94a3b8; }

				.vtm-search-spinner {
					flex-shrink: 0;
					width: 14px;
					height: 14px;
					border-radius: 999px;
					border: 2px solid rgba(148, 163, 184, 0.35);
					border-top-color: #64748b;
					animation: vtm-spin 0.7s linear infinite;
				}
				@keyframes vtm-spin { to { transform: rotate(360deg); } }

				.vtm-search-clear,
				.vtm-search-close {
					display: flex;
					align-items: center;
					justify-content: center;
					flex-shrink: 0;
					width: 26px;
					height: 26px;
					border-radius: 999px;
					border: none;
					background: rgba(148, 163, 184, 0.14);
					cursor: pointer;
					transition: background 0.15s ease;
				}
				.vtm-search-clear:hover,
				.vtm-search-close:hover { background: rgba(148, 163, 184, 0.28); }

				.vtm-search-suggestions {
					position: absolute;
					top: calc(100% + 8px);
					right: 0;
					width: min(340px, 100%);
					max-height: 280px;
					overflow-y: auto;
					list-style: none;
					margin: 0;
					padding: 6px;
					border-radius: 16px;
					background: rgba(255, 255, 255, 0.98);
					backdrop-filter: blur(10px);
					box-shadow: 0 14px 34px rgba(15, 23, 42, 0.22);
				}
				.vtm-search-suggestion {
					display: flex;
					align-items: flex-start;
					gap: 8px;
					width: 100%;
					padding: 8px 10px;
					border: none;
					background: transparent;
					border-radius: 10px;
					text-align: left;
					cursor: pointer;
					transition: background 0.12s ease;
				}
				.vtm-search-suggestion:hover { background: rgba(147, 51, 234, 0.08); }
				.vtm-search-suggestion-pin { flex-shrink: 0; margin-top: 3px; }
				.vtm-search-suggestion-text {
					display: flex;
					flex-direction: column;
					gap: 1px;
					min-width: 0;
				}
				.vtm-search-suggestion-main {
					font: 600 13px/1.3 'Inter', system-ui, sans-serif;
					color: #0f172a;
					white-space: nowrap;
					overflow: hidden;
					text-overflow: ellipsis;
				}
				.vtm-search-suggestion-sub {
					font: 500 11px/1.3 'Inter', system-ui, sans-serif;
					color: #94a3b8;
					white-space: nowrap;
					overflow: hidden;
					text-overflow: ellipsis;
				}

				@media (max-width: 480px) {
					.vtm-search-control { right: 108px; }
					.vtm-search-control--open { max-width: calc(100% - 122px); }
					.vtm-search-bar { width: 100%; }
					.vtm-search-suggestions { width: 100%; }
				}

				/* Marqueur véhicule */
				.vtm-marker-inner {
					position: relative;
					display: flex;
					align-items: center;
					justify-content: center;
				}
				.vtm-dot {
					width: 70%;
					height: 70%;
					border-radius: 999px;
					border: 3px solid white;
					display: flex;
					align-items: center;
					justify-content: center;
					box-shadow: 0 8px 18px rgba(15, 23, 42, 0.35);
					transition: transform 0.4s ease;
				}
				.vtm-pulse {
					position: absolute;
					inset: 0;
					border-radius: 999px;
					background: var(--vtm-color);
					opacity: 0.35;
					animation: vtm-pulse-anim 1.8s ease-out infinite;
				}
				@keyframes vtm-pulse-anim {
					0% { transform: scale(0.6); opacity: 0.45; }
					100% { transform: scale(1.9); opacity: 0; }
				}

				/* Marqueur résultat de recherche */
				.vtm-search-pin {
					filter: drop-shadow(0 8px 10px rgba(147, 51, 234, 0.4));
					animation: vtm-search-pin-drop 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
				}
				@keyframes vtm-search-pin-drop {
					from { transform: translateY(-14px); opacity: 0; }
					to { transform: translateY(0); opacity: 1; }
				}

				/* Popup moderne */
				.leaflet-popup-content-wrapper {
					border-radius: 14px;
					box-shadow: 0 14px 34px rgba(15, 23, 42, 0.2);
				}
				.leaflet-popup-content { margin: 12px 14px; }
				.vtm-popup-title {
					font: 700 14px/1.3 'Inter', system-ui, sans-serif;
					color: #0f172a;
					margin-bottom: 4px;
				}
				.vtm-popup-row {
					font: 500 12px/1.5 'Inter', system-ui, sans-serif;
					color: #64748b;
					display: flex;
					align-items: center;
					gap: 6px;
				}
			`}),(0,d.jsxs)(`div`,{className:`vtm-topbar`,children:[(0,d.jsx)(`span`,{className:`vtm-count-dot`}),e.length,` véhicule`,e.length>1?`s`:``,` suivi`,e.length>1?`s`:``]}),(0,d.jsx)(`button`,{type:`button`,className:`vtm-recenter-btn`,title:`Recentrer la carte`,onClick:()=>m(e=>e+1),children:(0,d.jsxs)(`svg`,{width:`18`,height:`18`,viewBox:`0 0 24 24`,fill:`none`,xmlns:`http://www.w3.org/2000/svg`,children:[(0,d.jsx)(`path`,{d:`M12 2v3M12 19v3M2 12h3M19 12h3`,stroke:`#0f172a`,strokeWidth:`2`,strokeLinecap:`round`}),(0,d.jsx)(`circle`,{cx:`12`,cy:`12`,r:`5.5`,stroke:`#0f172a`,strokeWidth:`2`})]})}),(0,d.jsx)(`button`,{type:`button`,className:`vtm-fullscreen-btn`,title:v?`Quitter le plein écran`:`Plein écran`,onClick:()=>{document.fullscreenElement?document.exitFullscreen?.():b.current?.requestFullscreen?.()},children:v?(0,d.jsx)(`svg`,{width:`18`,height:`18`,viewBox:`0 0 24 24`,fill:`none`,xmlns:`http://www.w3.org/2000/svg`,children:(0,d.jsx)(`path`,{d:`M9 4v3a2 2 0 0 1-2 2H4M20 9h-3a2 2 0 0 1-2-2V4M4 15h3a2 2 0 0 1 2 2v3M15 20v-3a2 2 0 0 1 2-2h3`,stroke:`#0f172a`,strokeWidth:`2`,strokeLinecap:`round`,strokeLinejoin:`round`})}):(0,d.jsx)(`svg`,{width:`18`,height:`18`,viewBox:`0 0 24 24`,fill:`none`,xmlns:`http://www.w3.org/2000/svg`,children:(0,d.jsx)(`path`,{d:`M4 9V6a2 2 0 0 1 2-2h3M15 4h3a2 2 0 0 1 2 2v3M20 15v3a2 2 0 0 1-2 2h-3M9 20H6a2 2 0 0 1-2-2v-3`,stroke:`#0f172a`,strokeWidth:`2`,strokeLinecap:`round`,strokeLinejoin:`round`})})}),(0,d.jsxs)(i,{center:x,zoom:13,zoomControl:!1,className:`vehicle-tracking-map`,children:[(0,d.jsx)(c,{url:`https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png`,attribution:`© OpenStreetMap contributors`}),(0,d.jsx)(h,{locations:e,selectedVehicleId:t},u),(0,d.jsx)(g,{}),e.map(e=>{let i=String(e.vehicleId),a=n[i],c=String(t)===i,l=c?`#16a34a`:r;return(0,d.jsx)(s,{position:[e.latitude,e.longitude],icon:p({color:l,selected:c,heading:e.heading??0}),children:(0,d.jsxs)(o,{children:[(0,d.jsx)(`div`,{className:`vtm-popup-title`,children:a?.registration??`Véhicule ${i}`}),(0,d.jsxs)(`div`,{className:`vtm-popup-row`,children:[`📍 `,e.latitude.toFixed(5),`, `,e.longitude.toFixed(5)]}),(0,d.jsxs)(`div`,{className:`vtm-popup-row`,children:[`🕒 `,e.timestamp?_(e.timestamp):`MAJ inconnue`]})]})},i)})]})]})};export{v as t};