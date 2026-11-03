/* EDF Zen Flex Card 0.0.5 — no external dependencies */
const DAY_ICONS={eco:'mdi:cash',sobriete:'mdi:cash-multiple',bonus:'mdi:piggy-bank'};
const RATE_ICONS={eco_hc:'mdi:weather-night',eco_hp:'mdi:weather-sunny',sobriete_hc:'mdi:moon-waning-crescent',sobriete_hp:'mdi:white-balance-sunny'};
const ICON=(name)=>{const el=document.createElement('ha-icon');el.setAttribute('icon',name);el.style.cssText='--mdc-icon-size:26px;vertical-align:middle;margin-right:8px;flex-shrink:0';return el;};
const LABELS={eco:'Éco',sobriete:'Sobriété',bonus:'Bonus'};
class ZenFlexCard extends HTMLElement {
  constructor(){super();this.attachShadow({mode:'open'});this._month=null;this._signature=null;}
  setConfig(config){if(!['compact','full'].includes(config.mode||'full'))throw Error('mode : compact ou full');this.config={show_tariffs:true,show_remaining:true,...config,mode:config.mode||'full',title:config.title||'EDF Zen Flex'};this._signature=null;this.render();}
  set hass(hass){this._hass=hass;this.toggleAttribute('data-dark',Boolean(hass.themes?.darkMode));this.render();}
  getCardSize(){return this.config?.mode==='compact'?5:13;}
  static getStubConfig(){return {type:'custom:zen-flex-card',mode:'full'};}
  static getConfigElement(){return document.createElement('zen-flex-card-editor');}
  render(){
    if(!this.config||!this._hass)return;
    const id=this.config.entity||Object.keys(this._hass.states).find(k=>this._hass.states[k].attributes.zen_flex_card);
    const state=this._hass.states[id],a=state?.attributes||{};
    const signature=JSON.stringify([id,state,this.config,this._month]);if(signature===this._signature)return;this._signature=signature;
    const root=this.shadowRoot;
    if(!root.firstChild){root.innerHTML=`<style>
:host{display:block;--zf-green:#168c66;--zf-red:#d84b60;--zf-blue:#347fd1;--zf-surface:rgba(110,125,150,.09);--zf-surface-border:rgba(105,120,150,.18);--zf-soft:rgba(100,120,150,.06);--zf-eco-bg:#C6ECDD;--zf-red-bg:#F9CCD3;--zf-blue-bg:#CCDEFF;--zf-price-bg:rgba(65,132,229,.065);--zf-current:#0099bf;--zf-active:#008fba;--zf-unknown-bg:#E7E9EE;--zf-unknown-text:#6B7280;--zf-unknown-border:#D1D5DD;--zf-eco-border:#72C9A4;--zf-red-border:#E998A7;--zf-blue-border:#8DB5F5}
:host([data-dark]){--zf-green:#46dfa4;--zf-red:#ff7183;--zf-blue:#75b9ff;--zf-surface:rgba(110,140,190,.13);--zf-surface-border:rgba(175,195,230,.16);--zf-soft:rgba(110,140,190,.09);--zf-eco-bg:#194F40;--zf-red-bg:#622D3D;--zf-blue-bg:#263E69;--zf-price-bg:rgba(73,112,177,.15);--zf-current:#ffb83f;--zf-active:#ffb83f;--zf-unknown-bg:#363943;--zf-unknown-text:#C4C9D4;--zf-unknown-border:#505562;--zf-eco-border:#35896D;--zf-red-border:#AA5168;--zf-blue-border:#4E79C3}
ha-card{box-sizing:border-box;padding:22px;border-radius:24px;overflow:hidden;background:var(--ha-card-background,var(--card-background-color));color:var(--primary-text-color);border:1px solid var(--divider-color);box-shadow:var(--ha-card-box-shadow,none)}
header{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:20px}.brand{font-size:22px;font-weight:700;letter-spacing:-.5px}.sub{font-size:11px;letter-spacing:1.3px;color:var(--secondary-text-color);margin-top:8px}
button{font:inherit;color:inherit;background:var(--zf-soft);border:1px solid var(--zf-surface-border);border-radius:11px;padding:8px 12px;cursor:pointer;touch-action:manipulation}button:focus-visible{outline:2px solid var(--primary-color)}.refresh{border-radius:50%;width:42px;height:42px;padding:0;font-size:23px}.refresh-icon{display:inline-block;line-height:1}.refresh.busy .refresh-icon{animation:zen-flex-spin .8s linear infinite}.refresh:disabled{opacity:.65}@keyframes zen-flex-spin{to{transform:rotate(360deg)}}@media(prefers-reduced-motion:reduce){.refresh.busy .refresh-icon{animation:none}}
.days{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.day{min-width:0;min-height:132px;box-sizing:border-box;border:1px solid var(--zf-surface-border);border-left:4px solid var(--zf-surface-border);border-radius:17px;padding:17px 14px;position:relative;overflow:hidden;background:var(--zf-surface)}.day:after{content:'';position:absolute;width:80px;height:80px;right:-35px;top:-35px;border:13px solid currentColor;border-radius:50%;opacity:.04;pointer-events:none}.day.eco{color:var(--zf-green);background:var(--zf-eco-bg);border-left-color:var(--zf-green)}.day.sobriete{color:var(--zf-red);background:var(--zf-red-bg);border-left-color:var(--zf-red)}.day.bonus{color:var(--zf-blue);background:var(--zf-blue-bg);border-left-color:var(--zf-blue)}.label{font-size:12px;letter-spacing:1px;text-transform:uppercase;color:var(--secondary-text-color)}.status{font-size:24px;font-weight:750;letter-spacing:-.5px;margin:13px 0 9px;display:flex;align-items:center;gap:5px;overflow-wrap:anywhere}.day:not(.eco):not(.sobriete):not(.bonus) .status{color:var(--primary-text-color)}.status ha-icon{--mdc-icon-size:27px!important;margin-right:4px!important}.dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--disabled-text-color);margin-right:6px;flex-shrink:0}.eco .dot{background:var(--zf-green)}.sobriete .dot{background:var(--zf-red)}.bonus .dot{background:var(--zf-blue)}.date{font-size:12px;color:var(--secondary-text-color)}
.counts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;margin:15px 0}.count{box-sizing:border-box;min-width:0;min-height:76px;border:1px solid var(--zf-surface-border);border-left:3px solid var(--zf-surface-border);border-radius:13px;padding:12px 14px;background:var(--zf-surface);display:flex;flex-direction:column;justify-content:center;align-items:flex-start}.count.eco{border-left-color:var(--zf-green)}.count.sobriete{border-left-color:var(--zf-red)}.count.bonus{grid-column:1/-1;border-left-color:var(--zf-blue)}.number{font-size:25px;font-weight:750;font-variant-numeric:tabular-nums}.count.eco .number{color:var(--zf-green)}.count.sobriete .number{color:var(--zf-red)}.count.bonus .number{color:var(--zf-blue)}.count small{display:flex;align-items:center;gap:4px;font-size:12px;line-height:1.35;color:var(--secondary-text-color);margin-top:5px}.count small ha-icon{--mdc-icon-size:18px!important;margin-right:3px!important}
.remaining{margin:0;padding:0}.remaining-note,.tariff-note{font-size:11px;line-height:1.6;color:var(--secondary-text-color);white-space:pre-line}.warning{color:var(--error-color);font-size:13px;margin:12px 0}.pricepanel{box-sizing:border-box;margin-top:14px;border:1px solid var(--zf-surface-border);border-radius:18px;padding:17px;background:var(--zf-price-bg)}.pricehead{display:flex;flex-direction:column;align-items:flex-start;gap:9px}.pricevalue{font-size:30px;line-height:1.2;letter-spacing:-.7px;font-weight:750}.badge{display:inline-flex;align-items:center;justify-content:center;vertical-align:middle;min-height:38px;box-sizing:border-box;font-size:13px;line-height:1.2;border-radius:10px;padding:5px 13px;margin-left:8px;background:var(--primary-color);color:var(--text-primary-color,#fff);white-space:nowrap}.badge ha-icon{--mdc-icon-size:27px!important;margin-right:9px!important}:host([data-dark]) .badge{background:rgba(130,170,235,.2);color:var(--primary-text-color);border:1px solid var(--zf-surface-border)}.rate-table{width:100%;border-collapse:collapse;margin-top:12px;font-size:13px;font-variant-numeric:tabular-nums}.rate-table th,.rate-table td{border-top:1px solid var(--zf-surface-border);padding:10px 4px;text-align:right;vertical-align:middle}.rate-table th:first-child,.rate-table td:first-child{text-align:left}.rate-table ha-icon{--mdc-icon-size:18px!important;margin-right:4px!important}.rate-highlight{font-weight:750;color:var(--zf-active)}.tariff-note{margin-top:9px}
.calendar{box-sizing:border-box;margin-top:19px;padding:15px;border:1px solid var(--zf-surface-border);border-radius:18px;background:var(--zf-soft)}.monthbar{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:12px}.monthname{font-size:15px;font-weight:650;text-transform:capitalize}.grid{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:5px;text-align:center}.weekday{font-size:11px;color:var(--secondary-text-color);padding:8px 0}.cell{box-sizing:border-box;padding:9px 0;border-radius:9px;font-size:13px;font-variant-numeric:tabular-nums;color:var(--primary-text-color);background:var(--zf-surface);border:1px solid var(--zf-surface-border)}.cell.eco{background:var(--zf-eco-bg);color:var(--zf-green);border-color:var(--zf-eco-border)}.cell.sobriete{background:var(--zf-red-bg);color:var(--zf-red);border-color:var(--zf-red-border)}.cell.bonus{background:var(--zf-blue-bg);color:var(--zf-blue);border-color:var(--zf-blue-border)}.cell.unknown{color:var(--zf-unknown-text);background:var(--zf-unknown-bg);border-color:var(--zf-unknown-border)}.cell.current{outline:2px solid var(--zf-current);outline-offset:0}.legend{display:flex;gap:12px;flex-wrap:wrap;font-size:11px;margin-top:14px}.legend .dot{margin-right:5px}[hidden]{display:none!important}
@media(max-width:450px){ha-card{padding:16px}.day{padding:14px 10px;min-height:125px}.status{font-size:21px}.status ha-icon{--mdc-icon-size:23px!important}.count{padding:12px 9px}.calendar{padding:11px}.rate-table{font-size:12px}.rate-table th,.rate-table td{padding:9px 2px}}
@media(max-width:350px){.status{font-size:19px}.day{padding:12px 8px}.count small{font-size:11px}}
</style><ha-card><header><div><div class="brand"></div><div class="sub"></div></div><button type="button" class="refresh" aria-label="Actualiser EDF"><span class="refresh-icon" aria-hidden="true">↻</span></button></header><div class="days"></div><div class="warning"></div><div class="counts"></div><section class="remaining"><div class="remaining-note"></div></section><section class="pricepanel"><div class="pricehead"><span>Prix actuel TTC <span class="badge"></span></span><span class="pricevalue"></span></div><div class="tariff-note"></div><table class="rate-table"><thead><tr><th>€/kWh TTC</th><th>HC</th><th>HP</th></tr></thead><tbody></tbody></table></section><section class="calendar"><div class="monthbar"><button type="button" class="prev" aria-label="Mois précédent">‹</button><span class="monthname"></span><button type="button" class="next" aria-label="Mois suivant">›</button></div><div class="grid"></div><div class="legend"><span class="eco"><i class="dot"></i>Éco</span><span class="sobriete"><i class="dot"></i>Sobriété</span><span class="bonus"><i class="dot"></i>Bonus</span><span>Gris : inconnu</span></div></section></ha-card>`;
      root.querySelector('.prev').onclick=()=>this.changeMonth(-1);root.querySelector('.next').onclick=()=>this.changeMonth(1);
      root.querySelector('.refresh').onclick=async()=>{
        if(!this._entity||this._refreshing)return;
        this._refreshing=true;
        const b=root.querySelector('.refresh');
        b.disabled=true;b.classList.add('busy');b.setAttribute('aria-busy','true');b.setAttribute('aria-label','Actualisation en cours');
        const visibleCycle=new Promise(resolve=>setTimeout(resolve,600));
        try{await this._hass.callService('homeassistant','update_entity',{entity_id:this._entity});}
        catch(e){root.querySelector('.warning').textContent=`Actualisation impossible : ${e.message||e}`;}
        finally{await visibleCycle;this._refreshing=false;b.disabled=false;b.classList.remove('busy');b.removeAttribute('aria-busy');b.setAttribute('aria-label','Actualiser EDF');}
      };
    }
    this._entity=id;
    root.querySelector('.brand').textContent=this.config.title;
    root.querySelector('.sub').textContent=`CALENDRIER ÉNERGIE · ${a.year||'—'}`;
    root.querySelector('.warning').textContent=!state?'Ajoutez l’intégration EDF Zen Flex.':['unavailable','unknown'].includes(state.state)?'Données EDF indisponibles — dernière observation affichée dans le calendrier.':'';
    const days=root.querySelector('.days');days.replaceChildren();
    for(const [label,status,date] of [['Aujourd’hui',state?.state,a.date],['Demain',state?.state==='unavailable'?null:a.tomorrow,a.tomorrow_date]]){
      const d=document.createElement('div');d.className=`day ${LABELS[status]?status:''}`;
      const l=document.createElement('div');l.className='label';l.textContent=label;
      const s=document.createElement('div');s.className='status';const dot=document.createElement('i');dot.className='dot';if(DAY_ICONS[status])s.append(ICON(DAY_ICONS[status]));else s.append(dot);s.append(document.createTextNode(LABELS[status]||'Inconnu'));
      const dt=document.createElement('div');dt.className='date';dt.textContent=this.dateLabel(date);d.append(l,s,dt);days.append(d);
    }
    const counts=root.querySelector('.counts');counts.replaceChildren();
    for(const [key,label,color] of [['eco_consumed','Éco passés','eco'],['eco_remaining','Éco restants','eco'],['sobriete_consumed','Sobriété passés','sobriete'],['sobriete_remaining','Sobriété restants','sobriete'],['bonus_consumed','Bonus passés','bonus']]){if(this.config.show_remaining===false&&key.endsWith('_remaining'))continue;const d=document.createElement('div');d.className=`count ${color}`;const n=document.createElement('div');n.className='number';n.textContent=a[key]??'—';const l=document.createElement('small');l.textContent=label;if(DAY_ICONS[color])l.prepend(ICON(DAY_ICONS[color]));d.append(n,l);counts.append(d);}
    root.querySelector('.remaining').hidden=this.config.show_remaining===false;
    const quality=a.history_quality;
    const countNotes=[];
    if(quality==='incoherent')countNotes.push('Compteurs incohérents : vérifiez les options.');
    else if(quality!=='complet')countNotes.push(`Historique incomplet : ${a.missing_days??'—'} jour(s) manquant(s).`);
    if(a.bonus_history_quality==='incoherent')countNotes.push('Compteur Bonus incohérent.');
    else if(a.bonus_history_quality==='incomplet'&&quality==='complet')countNotes.push('Compteur initial Bonus à renseigner.');
    root.querySelector('.remaining-note').textContent=countNotes.join('\n');
    root.querySelector('.remaining').hidden=!countNotes.length;
    const tariffs=a.tariffs||{},rates=tariffs.rates||{};
    const fmt=value=>typeof value==='number'&&Number.isFinite(value)?value.toLocaleString('fr-FR',{minimumFractionDigits:4,maximumFractionDigits:4}):'—';
    root.querySelector('.pricepanel').hidden=this.config.show_tariffs===false;
    const badge=root.querySelector('.badge');badge.replaceChildren();const dayKey=state?.state==='bonus'?'eco':state?.state;const priceIcon=RATE_ICONS[`${dayKey}_${tariffs.period}`];if(priceIcon)badge.append(ICON(priceIcon));badge.append(document.createTextNode(tariffs.period?.toUpperCase()||'—'));
    root.querySelector('.pricevalue').textContent=`${fmt(tariffs.current_price)} €/kWh`;
    const tariffNote=root.querySelector('.tariff-note');
    tariffNote.textContent=!tariffs.confirmed?'Tarifs à confirmer dans les options.':!tariffs.active?'Tarifs pas encore applicables.':tariffs.current_price==null?'Statut EDF du jour indisponible.':'';
    tariffNote.hidden=!tariffNote.textContent;
    const table=root.querySelector('.rate-table');table.hidden=this.config.mode==='compact';
    const tbody=table.querySelector('tbody');tbody.replaceChildren();
    for(const [key,label] of [['eco','Éco / Bonus'],['sobriete','Sobriété']]){const row=document.createElement('tr');const title=document.createElement('td');title.textContent=label;if(DAY_ICONS[key])title.prepend(ICON(DAY_ICONS[key]));row.append(title);for(const period of ['hc','hp']){const cell=document.createElement('td');cell.textContent=fmt(rates[`${key}_${period}`]);cell.prepend(ICON(RATE_ICONS[`${key}_${period}`]));if(tariffs.current_price!=null&&period===tariffs.period&&(state?.state===key||(key==='eco'&&state?.state==='bonus')))cell.className='rate-highlight';row.append(cell);}tbody.append(row);}
    root.querySelector('.calendar').hidden=this.config.mode==='compact';
    if(!this._month){const date=a.date||new Intl.DateTimeFormat('sv-SE',{timeZone:'Europe/Paris'}).format(new Date());this._month=date.slice(0,7);}
    const [year,month]=this._month.split('-').map(Number);
    root.querySelector('.monthname').textContent=new Date(year,month-1,1).toLocaleDateString('fr-FR',{month:'long',year:'numeric'});
    const grid=root.querySelector('.grid');grid.replaceChildren();for(const name of ['L','M','M','J','V','S','D']){const d=document.createElement('div');d.className='weekday';d.textContent=name;grid.append(d);}
    const offset=(new Date(year,month-1,1).getDay()+6)%7;for(let i=0;i<offset;i++)grid.append(document.createElement('span'));
    for(let day=1;day<=new Date(year,month,0).getDate();day++){const key=`${year}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}`,status=a.history?.[key]?.status;const d=document.createElement('div');d.className=`cell ${LABELS[status]?status:'unknown'} ${key===a.date?'current':''}`;d.textContent=day;d.title=`${this.dateLabel(key)} : ${LABELS[status]||'Inconnu'}`;grid.append(d);}

  }
  dateLabel(date){return date?new Date(`${date}T12:00:00`).toLocaleDateString('fr-FR',{weekday:'long',day:'numeric',month:'long'}):'Date inconnue';}
  changeMonth(delta){const [y,m]=this._month.split('-').map(Number);const date=new Date(y,m-1+delta,1);this._month=`${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}`;this.render();}
}
class ZenFlexEditor extends HTMLElement{
  constructor(){super();this._ready=false;this._updating=false;}
  setConfig(config){this.config={...config};this.render();}
  set hass(hass){this._hass=hass;this.updateEntities();}
  emit(key,value){
    if(this.config[key]===value)return;
    this.config={...this.config,[key]:value};
    this.dispatchEvent(new CustomEvent('config-changed',{detail:{config:{...this.config}},bubbles:true,composed:true}));
  }
  makeField(key,label,kind){
    const wrap=document.createElement('div');wrap.style.cssText='display:block;margin:14px 0';
    const caption=document.createElement('div');caption.textContent=label;caption.style.cssText='margin-bottom:6px;color:var(--secondary-text-color);font-size:14px';
    wrap.append(caption);
    const field=document.createElement(kind==='select'?'ha-selector':'ha-textfield');
    field.dataset.field=key;field.style.cssText='display:block;width:100%';
    if(kind==='select'){
      if(key==='mode')field.selector={select:{mode:'dropdown',options:[{value:'full',label:'Complet'},{value:'compact',label:'Compact'}]}};
      if(this._hass)field.hass=this._hass;
      field.addEventListener('value-changed',event=>{
        if(this._updating)return;
        const value=event.detail?.value;
        if(value!==undefined)this.emit(key,value);
      });
    }else{
      field.setAttribute('label',label);caption.remove();
      field.addEventListener('change',()=>this.emit(key,field.value));
    }
    wrap.append(field);this.append(wrap);return field;
  }
  updateEntities(){
    const picker=this.querySelector('[data-field="entity"]');
    if(!picker||!this._hass)return;
    picker.hass=this._hass;
    const current=this.config?.entity||'';
    const ids=Object.keys(this._hass.states).filter(id=>id.startsWith('sensor.')&&this._hass.states[id].attributes?.zen_flex_card);
    if(current&&!ids.includes(current))ids.unshift(current);
    const signature=ids.join('|');
    if(picker.dataset.signature===signature)return;
    picker.dataset.signature=signature;
    this._updating=true;
    picker.selector={select:{mode:'dropdown',options:[{value:'',label:'Détection automatique'},...ids.map(id=>({value:id,label:this._hass.states[id]?.attributes?.friendly_name||id}))]}};
    picker.value=current;
    this._updating=false;
  }
  render(){
    if(!this.config)return;
    // Ne pas recréer les sélecteurs : préserve le menu ouvert et la position sur Safari iOS.
    if(!this._ready){
      this._ready=true;
      this.makeField('title','Titre','text');
      this.makeField('entity','Entité Aujourd’hui','select');
      this.makeField('mode','Mode','select');
      for(const [key,label] of [['show_tariffs','Afficher les tarifs'],['show_remaining','Afficher les jours restants']]){
        const wrap=document.createElement('label');wrap.style.cssText='display:flex;align-items:center;gap:10px;margin:14px 0';
        const input=document.createElement('ha-switch');input.dataset.field=key;
        input.addEventListener('change',()=>this.emit(key,input.checked));
        wrap.append(input,document.createTextNode(label));this.append(wrap);
      }
    }
    this._updating=true;
    for(const key of ['title','mode','entity','show_tariffs','show_remaining']){
      const input=this.querySelector('[data-field="'+key+'"]');
      if(!input||input===document.activeElement)continue;
      if(key==='show_tariffs'||key==='show_remaining')input.checked=this.config[key]!==false;
      else input.value=this.config[key]||(key==='mode'?'full':'');
      if(input.localName==='ha-selector'&&this._hass)input.hass=this._hass;
    }
    this._updating=false;
    this.updateEntities();
  }
}
if(!customElements.get('zen-flex-card'))customElements.define('zen-flex-card',ZenFlexCard);
if(!customElements.get('zen-flex-card-editor'))customElements.define('zen-flex-card-editor',ZenFlexEditor);
window.customCards=window.customCards||[];window.customCards.push({type:'zen-flex-card',name:'EDF Zen Flex',description:'Calendrier, tarifs et jours Sobriété restants',preview:true});
