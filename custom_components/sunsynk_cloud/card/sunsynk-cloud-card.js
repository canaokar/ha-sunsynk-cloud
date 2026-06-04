function t(t,e,s,i){var r,n=arguments.length,o=n<3?e:null===i?i=Object.getOwnPropertyDescriptor(e,s):i;if("object"==typeof Reflect&&"function"==typeof Reflect.decorate)o=Reflect.decorate(t,e,s,i);else for(var a=t.length-1;a>=0;a--)(r=t[a])&&(o=(n<3?r(o):n>3?r(e,s,o):r(e,s))||o);return n>3&&o&&Object.defineProperty(e,s,o),o}"function"==typeof SuppressedError&&SuppressedError;
/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const e=globalThis,s=e.ShadowRoot&&(void 0===e.ShadyCSS||e.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,i=Symbol(),r=new WeakMap;let n=class{constructor(t,e,s){if(this._$cssResult$=!0,s!==i)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o;const e=this.t;if(s&&void 0===t){const s=void 0!==e&&1===e.length;s&&(t=r.get(e)),void 0===t&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),s&&r.set(e,t))}return t}toString(){return this.cssText}};const o=s?t=>t:t=>t instanceof CSSStyleSheet?(t=>{let e="";for(const s of t.cssRules)e+=s.cssText;return(t=>new n("string"==typeof t?t:t+"",void 0,i))(e)})(t):t,{is:a,defineProperty:c,getOwnPropertyDescriptor:l,getOwnPropertyNames:h,getOwnPropertySymbols:d,getPrototypeOf:p}=Object,u=globalThis,_=u.trustedTypes,g=_?_.emptyScript:"",$=u.reactiveElementPolyfillSupport,v=(t,e)=>t,m={toAttribute(t,e){switch(e){case Boolean:t=t?g:null;break;case Object:case Array:t=null==t?t:JSON.stringify(t)}return t},fromAttribute(t,e){let s=t;switch(e){case Boolean:s=null!==t;break;case Number:s=null===t?null:Number(t);break;case Object:case Array:try{s=JSON.parse(t)}catch(t){s=null}}return s}},f=(t,e)=>!a(t,e),y={attribute:!0,type:String,converter:m,reflect:!1,useDefault:!1,hasChanged:f};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */Symbol.metadata??=Symbol("metadata"),u.litPropertyMetadata??=new WeakMap;let b=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=y){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){const s=Symbol(),i=this.getPropertyDescriptor(t,s,e);void 0!==i&&c(this.prototype,t,i)}}static getPropertyDescriptor(t,e,s){const{get:i,set:r}=l(this.prototype,t)??{get(){return this[e]},set(t){this[e]=t}};return{get:i,set(e){const n=i?.call(this);r?.call(this,e),this.requestUpdate(t,n,s)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??y}static _$Ei(){if(this.hasOwnProperty(v("elementProperties")))return;const t=p(this);t.finalize(),void 0!==t.l&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(v("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(v("properties"))){const t=this.properties,e=[...h(t),...d(t)];for(const s of e)this.createProperty(s,t[s])}const t=this[Symbol.metadata];if(null!==t){const e=litPropertyMetadata.get(t);if(void 0!==e)for(const[t,s]of e)this.elementProperties.set(t,s)}this._$Eh=new Map;for(const[t,e]of this.elementProperties){const s=this._$Eu(t,e);void 0!==s&&this._$Eh.set(s,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){const e=[];if(Array.isArray(t)){const s=new Set(t.flat(1/0).reverse());for(const t of s)e.unshift(o(t))}else void 0!==t&&e.push(o(t));return e}static _$Eu(t,e){const s=e.attribute;return!1===s?void 0:"string"==typeof s?s:"string"==typeof t?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),void 0!==this.renderRoot&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){const t=new Map,e=this.constructor.elementProperties;for(const s of e.keys())this.hasOwnProperty(s)&&(t.set(s,this[s]),delete this[s]);t.size>0&&(this._$Ep=t)}createRenderRoot(){const t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return((t,i)=>{if(s)t.adoptedStyleSheets=i.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(const s of i){const i=document.createElement("style"),r=e.litNonce;void 0!==r&&i.setAttribute("nonce",r),i.textContent=s.cssText,t.appendChild(i)}})(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,s){this._$AK(t,s)}_$ET(t,e){const s=this.constructor.elementProperties.get(t),i=this.constructor._$Eu(t,s);if(void 0!==i&&!0===s.reflect){const r=(void 0!==s.converter?.toAttribute?s.converter:m).toAttribute(e,s.type);this._$Em=t,null==r?this.removeAttribute(i):this.setAttribute(i,r),this._$Em=null}}_$AK(t,e){const s=this.constructor,i=s._$Eh.get(t);if(void 0!==i&&this._$Em!==i){const t=s.getPropertyOptions(i),r="function"==typeof t.converter?{fromAttribute:t.converter}:void 0!==t.converter?.fromAttribute?t.converter:m;this._$Em=i;const n=r.fromAttribute(e,t.type);this[i]=n??this._$Ej?.get(i)??n,this._$Em=null}}requestUpdate(t,e,s,i=!1,r){if(void 0!==t){const n=this.constructor;if(!1===i&&(r=this[t]),s??=n.getPropertyOptions(t),!((s.hasChanged??f)(r,e)||s.useDefault&&s.reflect&&r===this._$Ej?.get(t)&&!this.hasAttribute(n._$Eu(t,s))))return;this.C(t,e,s)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(t,e,{useDefault:s,reflect:i,wrapped:r},n){s&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,n??e??this[t]),!0!==r||void 0!==n)||(this._$AL.has(t)||(this.hasUpdated||s||(e=void 0),this._$AL.set(t,e)),!0===i&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}const t=this.scheduleUpdate();return null!=t&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[t,e]of this._$Ep)this[t]=e;this._$Ep=void 0}const t=this.constructor.elementProperties;if(t.size>0)for(const[e,s]of t){const{wrapped:t}=s,i=this[e];!0!==t||this._$AL.has(e)||void 0===i||this.C(e,void 0,s,i)}}let t=!1;const e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(t=>t.hostUpdate?.()),this.update(e)):this._$EM()}catch(e){throw t=!1,this._$EM(),e}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(t){}firstUpdated(t){}};b.elementStyles=[],b.shadowRootOptions={mode:"open"},b[v("elementProperties")]=new Map,b[v("finalized")]=new Map,$?.({ReactiveElement:b}),(u.reactiveElementVersions??=[]).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const S=globalThis,w=t=>t,A=S.trustedTypes,x=A?A.createPolicy("lit-html",{createHTML:t=>t}):void 0,E="$lit$",C=`lit$${Math.random().toFixed(9).slice(2)}$`,P="?"+C,k=`<${P}>`,O=document,T=()=>O.createComment(""),U=t=>null===t||"object"!=typeof t&&"function"!=typeof t,M=Array.isArray,N="[ \t\n\f\r]",H=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,R=/-->/g,j=/>/g,z=RegExp(`>|${N}(?:([^\\s"'>=/]+)(${N}*=${N}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),D=/'/g,L=/"/g,W=/^(?:script|style|textarea|title)$/i,B=(t=>(e,...s)=>({_$litType$:t,strings:e,values:s}))(1),I=Symbol.for("lit-noChange"),F=Symbol.for("lit-nothing"),q=new WeakMap,G=O.createTreeWalker(O,129);function V(t,e){if(!M(t)||!t.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==x?x.createHTML(e):e}const Z=(t,e)=>{const s=t.length-1,i=[];let r,n=2===e?"<svg>":3===e?"<math>":"",o=H;for(let e=0;e<s;e++){const s=t[e];let a,c,l=-1,h=0;for(;h<s.length&&(o.lastIndex=h,c=o.exec(s),null!==c);)h=o.lastIndex,o===H?"!--"===c[1]?o=R:void 0!==c[1]?o=j:void 0!==c[2]?(W.test(c[2])&&(r=RegExp("</"+c[2],"g")),o=z):void 0!==c[3]&&(o=z):o===z?">"===c[0]?(o=r??H,l=-1):void 0===c[1]?l=-2:(l=o.lastIndex-c[2].length,a=c[1],o=void 0===c[3]?z:'"'===c[3]?L:D):o===L||o===D?o=z:o===R||o===j?o=H:(o=z,r=void 0);const d=o===z&&t[e+1].startsWith("/>")?" ":"";n+=o===H?s+k:l>=0?(i.push(a),s.slice(0,l)+E+s.slice(l)+C+d):s+C+(-2===l?e:d)}return[V(t,n+(t[s]||"<?>")+(2===e?"</svg>":3===e?"</math>":"")),i]};class J{constructor({strings:t,_$litType$:e},s){let i;this.parts=[];let r=0,n=0;const o=t.length-1,a=this.parts,[c,l]=Z(t,e);if(this.el=J.createElement(c,s),G.currentNode=this.el.content,2===e||3===e){const t=this.el.content.firstChild;t.replaceWith(...t.childNodes)}for(;null!==(i=G.nextNode())&&a.length<o;){if(1===i.nodeType){if(i.hasAttributes())for(const t of i.getAttributeNames())if(t.endsWith(E)){const e=l[n++],s=i.getAttribute(t).split(C),o=/([.?@])?(.*)/.exec(e);a.push({type:1,index:r,name:o[2],strings:s,ctor:"."===o[1]?tt:"?"===o[1]?et:"@"===o[1]?st:Y}),i.removeAttribute(t)}else t.startsWith(C)&&(a.push({type:6,index:r}),i.removeAttribute(t));if(W.test(i.tagName)){const t=i.textContent.split(C),e=t.length-1;if(e>0){i.textContent=A?A.emptyScript:"";for(let s=0;s<e;s++)i.append(t[s],T()),G.nextNode(),a.push({type:2,index:++r});i.append(t[e],T())}}}else if(8===i.nodeType)if(i.data===P)a.push({type:2,index:r});else{let t=-1;for(;-1!==(t=i.data.indexOf(C,t+1));)a.push({type:7,index:r}),t+=C.length-1}r++}}static createElement(t,e){const s=O.createElement("template");return s.innerHTML=t,s}}function K(t,e,s=t,i){if(e===I)return e;let r=void 0!==i?s._$Co?.[i]:s._$Cl;const n=U(e)?void 0:e._$litDirective$;return r?.constructor!==n&&(r?._$AO?.(!1),void 0===n?r=void 0:(r=new n(t),r._$AT(t,s,i)),void 0!==i?(s._$Co??=[])[i]=r:s._$Cl=r),void 0!==r&&(e=K(t,r._$AS(t,e.values),r,i)),e}class Q{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){const{el:{content:e},parts:s}=this._$AD,i=(t?.creationScope??O).importNode(e,!0);G.currentNode=i;let r=G.nextNode(),n=0,o=0,a=s[0];for(;void 0!==a;){if(n===a.index){let e;2===a.type?e=new X(r,r.nextSibling,this,t):1===a.type?e=new a.ctor(r,a.name,a.strings,this,t):6===a.type&&(e=new it(r,this,t)),this._$AV.push(e),a=s[++o]}n!==a?.index&&(r=G.nextNode(),n++)}return G.currentNode=O,i}p(t){let e=0;for(const s of this._$AV)void 0!==s&&(void 0!==s.strings?(s._$AI(t,s,e),e+=s.strings.length-2):s._$AI(t[e])),e++}}class X{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,s,i){this.type=2,this._$AH=F,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=s,this.options=i,this._$Cv=i?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode;const e=this._$AM;return void 0!==e&&11===t?.nodeType&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=K(this,t,e),U(t)?t===F||null==t||""===t?(this._$AH!==F&&this._$AR(),this._$AH=F):t!==this._$AH&&t!==I&&this._(t):void 0!==t._$litType$?this.$(t):void 0!==t.nodeType?this.T(t):(t=>M(t)||"function"==typeof t?.[Symbol.iterator])(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==F&&U(this._$AH)?this._$AA.nextSibling.data=t:this.T(O.createTextNode(t)),this._$AH=t}$(t){const{values:e,_$litType$:s}=t,i="number"==typeof s?this._$AC(t):(void 0===s.el&&(s.el=J.createElement(V(s.h,s.h[0]),this.options)),s);if(this._$AH?._$AD===i)this._$AH.p(e);else{const t=new Q(i,this),s=t.u(this.options);t.p(e),this.T(s),this._$AH=t}}_$AC(t){let e=q.get(t.strings);return void 0===e&&q.set(t.strings,e=new J(t)),e}k(t){M(this._$AH)||(this._$AH=[],this._$AR());const e=this._$AH;let s,i=0;for(const r of t)i===e.length?e.push(s=new X(this.O(T()),this.O(T()),this,this.options)):s=e[i],s._$AI(r),i++;i<e.length&&(this._$AR(s&&s._$AB.nextSibling,i),e.length=i)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){const e=w(t).nextSibling;w(t).remove(),t=e}}setConnected(t){void 0===this._$AM&&(this._$Cv=t,this._$AP?.(t))}}class Y{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,s,i,r){this.type=1,this._$AH=F,this._$AN=void 0,this.element=t,this.name=e,this._$AM=i,this.options=r,s.length>2||""!==s[0]||""!==s[1]?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=F}_$AI(t,e=this,s,i){const r=this.strings;let n=!1;if(void 0===r)t=K(this,t,e,0),n=!U(t)||t!==this._$AH&&t!==I,n&&(this._$AH=t);else{const i=t;let o,a;for(t=r[0],o=0;o<r.length-1;o++)a=K(this,i[s+o],e,o),a===I&&(a=this._$AH[o]),n||=!U(a)||a!==this._$AH[o],a===F?t=F:t!==F&&(t+=(a??"")+r[o+1]),this._$AH[o]=a}n&&!i&&this.j(t)}j(t){t===F?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}}class tt extends Y{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===F?void 0:t}}class et extends Y{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==F)}}class st extends Y{constructor(t,e,s,i,r){super(t,e,s,i,r),this.type=5}_$AI(t,e=this){if((t=K(this,t,e,0)??F)===I)return;const s=this._$AH,i=t===F&&s!==F||t.capture!==s.capture||t.once!==s.once||t.passive!==s.passive,r=t!==F&&(s===F||i);i&&this.element.removeEventListener(this.name,this,s),r&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}}class it{constructor(t,e,s){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=s}get _$AU(){return this._$AM._$AU}_$AI(t){K(this,t)}}const rt=S.litHtmlPolyfillSupport;rt?.(J,X),(S.litHtmlVersions??=[]).push("3.3.3");const nt=globalThis;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */class ot extends b{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){const e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=((t,e,s)=>{const i=s?.renderBefore??e;let r=i._$litPart$;if(void 0===r){const t=s?.renderBefore??null;i._$litPart$=r=new X(e.insertBefore(T(),t),t,void 0,s??{})}return r._$AI(t),r})(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return I}}ot._$litElement$=!0,ot.finalized=!0,nt.litElementHydrateSupport?.({LitElement:ot});const at=nt.litElementPolyfillSupport;at?.({LitElement:ot}),(nt.litElementVersions??=[]).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const ct={attribute:!0,type:String,converter:m,reflect:!1,hasChanged:f},lt=(t=ct,e,s)=>{const{kind:i,metadata:r}=s;let n=globalThis.litPropertyMetadata.get(r);if(void 0===n&&globalThis.litPropertyMetadata.set(r,n=new Map),"setter"===i&&((t=Object.create(t)).wrapped=!0),n.set(s.name,t),"accessor"===i){const{name:i}=s;return{set(s){const r=e.get.call(this);e.set.call(this,s),this.requestUpdate(i,r,t,!0,s)},init(e){return void 0!==e&&this.C(i,void 0,t,e),e}}}if("setter"===i){const{name:i}=s;return function(s){const r=this[i];e.call(this,s),this.requestUpdate(i,r,t,!0,s)}}throw Error("Unsupported decorator location: "+i)};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */function ht(t){return(e,s)=>"object"==typeof s?lt(t,e,s):((t,e,s)=>{const i=e.hasOwnProperty(s);return e.constructor.createProperty(s,t),i?Object.getOwnPropertyDescriptor(e,s):void 0})(t,e,s)}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */function dt(t){return ht({...t,state:!0,attribute:!1})}const pt=((t,...e)=>{const s=1===t.length?t[0]:e.reduce((e,s,i)=>e+(t=>{if(!0===t._$cssResult$)return t.cssText;if("number"==typeof t)return t;throw Error("Value passed to 'css' function must be a 'css' function result: "+t+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(s)+t[i+1],t[0]);return new n(s,t,i)})`
  :host {
    --primary-color: #4fc3f7;
    --success-color: #66bb6a;
    --warning-color: #ffa726;
    --error-color: #ef5350;
    --card-bg: var(--ha-card-background, #fff);
    --text-primary: var(--primary-text-color, #212121);
    --text-secondary: var(--secondary-text-color, #727272);
    --divider: var(--divider-color, #e0e0e0);
  }

  ha-card {
    padding: 16px;
  }

  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
  }

  .header .title {
    font-size: 18px;
    font-weight: 500;
    color: var(--text-primary);
  }

  .header .status {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--success-color);
  }

  .status-dot.offline {
    background: var(--error-color);
  }

  .power-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 16px;
  }

  .power-tile {
    text-align: center;
    padding: 12px 8px;
    border-radius: 8px;
    background: var(--card-bg);
    border: 1px solid var(--divider);
  }

  .power-tile .value {
    font-size: 20px;
    font-weight: 600;
  }

  .power-tile .label {
    font-size: 11px;
    color: var(--text-secondary);
    margin-top: 4px;
  }

  .section {
    border-top: 1px solid var(--divider);
    padding-top: 12px;
    margin-top: 12px;
  }

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    cursor: pointer;
    user-select: none;
    padding: 4px 0;
  }

  .section-header h3 {
    margin: 0;
    font-size: 14px;
    font-weight: 500;
  }

  .section-content {
    padding-top: 12px;
  }

  .setting-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 0;
  }

  .setting-row .label {
    font-size: 14px;
    color: var(--text-primary);
  }

  .timeline-bar {
    position: relative;
    height: 48px;
    background: var(--divider);
    border-radius: 6px;
    overflow: hidden;
    margin: 12px 0;
  }

  .timeline-slot {
    position: absolute;
    top: 0;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    color: white;
    cursor: pointer;
    transition: opacity 0.2s;
    border-right: 1px solid rgba(255, 255, 255, 0.3);
  }

  .timeline-slot:hover {
    opacity: 0.85;
  }

  .timeline-slot.grid-charge {
    background: #1e88e5;
  }

  .timeline-slot.solar {
    background: #43a047;
  }

  .timeline-slot.disabled {
    background: #9e9e9e;
  }

  .timeline-labels {
    display: flex;
    justify-content: space-between;
    font-size: 10px;
    color: var(--text-secondary);
    padding: 0 2px;
  }

  .day-row {
    display: flex;
    gap: 6px;
    margin: 8px 0;
  }

  .day-toggle {
    width: 36px;
    height: 28px;
    border-radius: 4px;
    border: 1px solid var(--divider);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    cursor: pointer;
    user-select: none;
  }

  .day-toggle.active {
    background: var(--primary-color);
    color: white;
    border-color: var(--primary-color);
  }

  .save-bar {
    display: flex;
    gap: 8px;
    justify-content: flex-end;
    margin-top: 12px;
  }

  .soc-badge {
    font-size: 24px;
    font-weight: 700;
  }
`;let ut=class extends ot{constructor(){super(...arguments),this._expandedSections=new Set(["timers"])}setConfig(t){if(!t.device)throw new Error("Please define a device (inverter SN)");this._config={show_realtime:!0,show_timers:!0,show_battery:!0,show_grid:!0,compact:!1,...t}}_prefix(){return`sunsynk_${this._config.device}`}_getState(t,e){const s=`${t}.${this._prefix()}_${e}`;return this.hass?.states[s]?.state}_getNumericState(t,e){const s=this._getState(t,e);if(void 0!==s&&"unavailable"!==s&&"unknown"!==s)return parseFloat(s)}async _callService(t,e,s,i){await this.hass.callService(t,e,i,{entity_id:s})}_toggleSection(t){const e=new Set(this._expandedSections);e.has(t)?e.delete(t):e.add(t),this._expandedSections=e}render(){return this._config&&this.hass?B`
      <ha-card>
        ${this._renderHeader()}
        ${this._config.show_realtime?this._renderPowerTiles():F}
        ${this._renderSettingsSection()}
        ${this._config.show_timers?this._renderTimerSection():F}
        ${this._config.show_battery?this._renderBatterySection():F}
        ${this._config.show_grid?this._renderGridSection():F}
      </ha-card>
    `:F}_renderHeader(){const t=this._getNumericState("sensor","battery_soc");return B`
      <div class="header">
        <span class="title">Sunsynk Inverter</span>
        <div class="status">
          <span class="soc-badge"
            >${null!=t?`${Math.round(t)}%`:"--"}</span
          >
        </div>
      </div>
    `}_renderPowerTiles(){const t=this._getNumericState("sensor","pv_power"),e=this._getNumericState("sensor","battery_power"),s=this._getNumericState("sensor","grid_power"),i=this._getNumericState("sensor","load_power");return B`
      <div class="power-grid">
        <div class="power-tile">
          <div class="value" style="color: #f9a825">${t??"--"}W</div>
          <div class="label">PV</div>
        </div>
        <div class="power-tile">
          <div
            class="value"
            style="color: ${(e??0)>0?"#ef5350":"#66bb6a"}"
          >
            ${e??"--"}W
          </div>
          <div class="label">Battery</div>
        </div>
        <div class="power-tile">
          <div
            class="value"
            style="color: ${(s??0)<0?"#66bb6a":"#ef5350"}"
          >
            ${s??"--"}W
          </div>
          <div class="label">Grid</div>
        </div>
        <div class="power-tile">
          <div class="value">${i??"--"}W</div>
          <div class="label">Load</div>
        </div>
      </div>
    `}_renderSettingsSection(){const t=this._getState("select","work_mode"),e=this._getState("select","energy_mode"),s=this._getState("switch","solar_sell");return B`
      <div class="section">
        <div
          class="section-header"
          @click=${()=>this._toggleSection("settings")}
        >
          <h3>Work Mode & General</h3>
          <span>${this._expandedSections.has("settings")?"▾":"▸"}</span>
        </div>
        ${this._expandedSections.has("settings")?B`
              <div class="section-content">
                <div class="setting-row">
                  <span class="label">Work Mode</span>
                  <ha-select
                    .value=${t}
                    @selected=${t=>{const e=`select.${this._prefix()}_work_mode`;this._callService("select","select_option",e,{option:t.target.value})}}
                  >
                    <mwc-list-item value="Selling First"
                      >Selling First</mwc-list-item
                    >
                    <mwc-list-item value="Zero Export"
                      >Zero Export</mwc-list-item
                    >
                    <mwc-list-item value="Limited to Home"
                      >Limited to Home</mwc-list-item
                    >
                  </ha-select>
                </div>
                <div class="setting-row">
                  <span class="label">Energy Mode</span>
                  <ha-select
                    .value=${e}
                    @selected=${t=>{const e=`select.${this._prefix()}_energy_mode`;this._callService("select","select_option",e,{option:t.target.value})}}
                  >
                    <mwc-list-item value="Battery First"
                      >Battery First</mwc-list-item
                    >
                    <mwc-list-item value="Load First"
                      >Load First</mwc-list-item
                    >
                  </ha-select>
                </div>
                <div class="setting-row">
                  <span class="label">Solar Sell</span>
                  <ha-switch
                    .checked=${"on"===s}
                    @change=${t=>{const e=`switch.${this._prefix()}_solar_sell`,s=t.target.checked?"turn_on":"turn_off";this._callService("switch",s,e)}}
                  ></ha-switch>
                </div>
              </div>
            `:F}
      </div>
    `}_renderTimerSection(){const t=[];for(let e=1;e<=6;e++)t.push({index:e,enabled:"on"===this._getState("switch",`timer_${e}_enable`),endTime:this._getState("time",`timer_${e}_end_time`)??"00:00",power:this._getNumericState("number",`timer_${e}_power`)??0,soc:this._getNumericState("number",`timer_${e}_soc`)??0,gridCharge:"on"===this._getState("switch",`timer_${e}_grid_charge`)});const e=["00:00",...t.slice(0,5).map(t=>t.endTime)];return B`
      <div class="section">
        <div
          class="section-header"
          @click=${()=>this._toggleSection("timers")}
        >
          <h3>Timer Schedule</h3>
          <span>${this._expandedSections.has("timers")?"▾":"▸"}</span>
        </div>
        ${this._expandedSections.has("timers")?B`
              <div class="section-content">
                <div class="timeline-bar">
                  ${t.map((t,s)=>{const i=this._timeToPercent(e[s]),r=this._timeToPercent(t.endTime)-i,n=t.enabled?t.gridCharge?"grid-charge":"solar":"disabled";return B`
                      <div
                        class="timeline-slot ${n}"
                        style="left: ${i}%; width: ${r}%"
                        title="Slot ${t.index}: ${e[s]}-${t.endTime} | ${t.power}W | SOC ${t.soc}%"
                      >
                        <span>${t.soc}%</span>
                        <span>${t.power}W</span>
                      </div>
                    `})}
                </div>
                <div class="timeline-labels">
                  <span>00:00</span><span>06:00</span><span>12:00</span
                  ><span>18:00</span><span>24:00</span>
                </div>
                ${this._renderDayRow()}
              </div>
            `:F}
      </div>
    `}_renderDayRow(){return B`
      <div class="day-row">
        ${[{key:"monday",label:"Mo"},{key:"tuesday",label:"Tu"},{key:"wednesday",label:"We"},{key:"thursday",label:"Th"},{key:"friday",label:"Fr"},{key:"saturday",label:"Sa"},{key:"sunday",label:"Su"}].map(t=>{const e="on"===this._getState("switch",`schedule_${t.key}`);return B`
            <div
              class="day-toggle ${e?"active":""}"
              @click=${()=>{const s=`switch.${this._prefix()}_schedule_${t.key}`;this._callService("switch",e?"turn_off":"turn_on",s)}}
            >
              ${t.label}
            </div>
          `})}
      </div>
    `}_renderBatterySection(){return B`
      <div class="section">
        <div
          class="section-header"
          @click=${()=>this._toggleSection("battery")}
        >
          <h3>Battery</h3>
          <span>${this._expandedSections.has("battery")?"▾":"▸"}</span>
        </div>
        ${this._expandedSections.has("battery")?B`
              <div class="section-content">
                ${this._renderSlider("Shutdown SOC","number","battery_shutdown_soc","%",0,100)}
                ${this._renderSlider("Low Warning SOC","number","battery_low_soc","%",0,100)}
                ${this._renderSlider("Restart SOC","number","battery_restart_soc","%",0,100)}
                ${this._renderSlider("Max Charge Current","number","max_charge_current","A",0,280)}
                ${this._renderSlider("Max Discharge Current","number","max_discharge_current","A",0,280)}
              </div>
            `:F}
      </div>
    `}_renderGridSection(){const t=this._getState("switch","grid_charge"),e=this._getState("switch","grid_peak_shaving");return B`
      <div class="section">
        <div
          class="section-header"
          @click=${()=>this._toggleSection("grid")}
        >
          <h3>Grid</h3>
          <span>${this._expandedSections.has("grid")?"▾":"▸"}</span>
        </div>
        ${this._expandedSections.has("grid")?B`
              <div class="section-content">
                <div class="setting-row">
                  <span class="label">Grid Charge</span>
                  <ha-switch
                    .checked=${"on"===t}
                    @change=${t=>{const e=`switch.${this._prefix()}_grid_charge`;this._callService("switch",t.target.checked?"turn_on":"turn_off",e)}}
                  ></ha-switch>
                </div>
                ${this._renderSlider("Grid Charge SOC","number","grid_charge_soc","%",10,90)}
                ${this._renderSlider("Grid Charge Current","number","grid_charge_current","A",0,275)}
                <div class="setting-row">
                  <span class="label">Peak Shaving</span>
                  <ha-switch
                    .checked=${"on"===e}
                    @change=${t=>{const e=`switch.${this._prefix()}_grid_peak_shaving`;this._callService("switch",t.target.checked?"turn_on":"turn_off",e)}}
                  ></ha-switch>
                </div>
                ${this._renderSlider("Peak Shaving Power","number","grid_peak_power","W",0,15e3)}
              </div>
            `:F}
      </div>
    `}_renderSlider(t,e,s,i,r,n){const o=this._getNumericState(e,s),a=`${e}.${this._prefix()}_${s}`;return B`
      <div class="setting-row">
        <span class="label">${t}</span>
        <span>${null!=o?`${o}${i}`:"--"}</span>
      </div>
      <ha-slider
        .min=${r}
        .max=${n}
        .value=${o??r}
        @change=${t=>{const e=t.target.value;this._callService("number","set_value",a,{value:e})}}
      ></ha-slider>
    `}_timeToPercent(t){const[e,s]=t.split(":").map(Number);return(60*e+s)/1440*100}getCardSize(){return this._config?.compact?4:8}static getStubConfig(){return{device:""}}};ut.styles=pt,t([ht({attribute:!1})],ut.prototype,"hass",void 0),t([dt()],ut.prototype,"_config",void 0),t([dt()],ut.prototype,"_expandedSections",void 0),ut=t([(t=>(e,s)=>{void 0!==s?s.addInitializer(()=>{customElements.define(t,e)}):customElements.define(t,e)})("sunsynk-cloud-card")],ut);const _t=window;_t.customCards=_t.customCards||[],_t.customCards.push({type:"sunsynk-cloud-card",name:"Sunsynk Cloud Card",description:"Control panel for Sunsynk/Deye inverters via cloud API"});export{ut as SunsynkCloudCard};
