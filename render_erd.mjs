import fs from "fs";

let doc;

class DOMNode {
  constructor(nodeType, tagName) {
    this.nodeType = nodeType;
    this.tagName = tagName;
    this._data = "";
    this.attrs = {};
    this.childNodes = [];
    this.style = {};
    this.classList = { add: () => {}, remove: () => {} };
  }

  get ownerDocument() { return doc; }

  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return this.attrs[k] || null; }
  hasAttribute(k) { return k in this.attrs; }
  removeAttribute(k) { delete this.attrs[k]; }

  appendChild(child) {
    this.childNodes.push(child);
    return child;
  }
  removeChild(child) {
    const idx = this.childNodes.indexOf(child);
    if (idx >= 0) this.childNodes.splice(idx, 1);
    return child;
  }

  get data() { return this._data; }
  set data(v) { this._data = String(v); }
  get nodeValue() { return this._data; }
  set nodeValue(v) { this._data = String(v); }
  get textContent() {
    if (this.nodeType === 3) return this._data;
    return this.childNodes.map(c => c.textContent).join("");
  }
  set textContent(v) {
    if (this.nodeType === 3) {
      this._data = String(v);
    } else {
      this.childNodes = [doc.createTextNode(v)];
    }
  }

  getContext() {
    return {
      measureText: (text) => ({ width: Math.max(10, ((text || "").length) * 8.5) }),
      font: "",
    };
  }

  getBBox() {
    const txt = this.textContent || "";
    return {
      x: 0,
      y: 0,
      width: Math.max(20, txt.length * 8.5),
      height: 18
    };
  }
}

doc = {
  createElement: (tag) => new DOMNode(1, tag),
  createElementNS: (ns, tag) => new DOMNode(1, tag),
  createTextNode: (text) => {
    const n = new DOMNode(3, null);
    n._data = text || "";
    return n;
  },
  createProcessingInstruction: (target, data) => ({ target, data, nodeType: 7, get ownerDocument() { return doc; } }),
  createComment: (text) => ({ text, nodeType: 8, get ownerDocument() { return doc; } }),
  getElementById: () => null,
  body: new DOMNode(1, "body"),
  documentElement: new DOMNode(1, "html"),
  implementation: {
    createDocument: () => doc
  }
};

globalThis.window = globalThis;
globalThis.document = doc;
globalThis.location = { href: "http://localhost/" };
globalThis._measureCanvas = doc.createElement("canvas");

function serializeNode(node) {
  if (!node) return "";
  if (node.nodeType === 3) {
    return (node._data || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  if (node.tagName) {
    let s = "<" + node.tagName;
    for (const k in (node.attrs || {})) {
      s += ` ${k}="${String(node.attrs[k]).replace(/&/g, "&amp;").replace(/\"/g, "&quot;")}"`;
    }
    s += ">";
    if (node.childNodes && node.childNodes.length > 0) {
      for (const c of node.childNodes) s += serializeNode(c);
    }
    s += `</${node.tagName}>`;
    return s;
  }
  return "";
}

globalThis.XMLSerializer = class {
  serializeToString(n) {
    return serializeNode(n) || "<svg></svg>";
  }
};

const pumlPath = process.argv[2] || "references/bab 4/ERD_PIXELT_FINAL.puml";
const svgPath = process.argv[3] || "references/bab 4/ERD_PIXELT_FINAL.svg";

const puml = fs.readFileSync(pumlPath, "utf8");

import("@plantuml/core").then(async ({ renderToString }) => {
  renderToString(puml.trim().split("\n"), (svg) => {
    fs.writeFileSync(svgPath, svg, "utf8");
    console.log(`Successfully generated ${svgPath}`);
  }, (err) => {
    console.error("PlantUML ERROR:", err);
  });
}).catch(err => console.error("Import ERROR:", err));

