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
      measureText: (text) => ({ width: Math.max(10, ((text || "").length) * 8.0) }),
      font: "",
    };
  }

  getBBox() {
    const txt = this.textContent || "";
    return {
      x: 0,
      y: 0,
      width: Math.max(20, txt.length * 8.0),
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

const puml = `@startuml sequence_diagram_doctor_profile
title Sequence Diagram Profil Dokter (Doctor Profile) - PIXEL-T

skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam sequenceMessageAlign center
skinparam responseMessageBelowArrow true
skinparam defaultFontName "Arial"
skinparam defaultFontSize 11
skinparam roundCorner 4
skinparam sequenceArrowThickness 1.2
hide footbox

skinparam actor {
    BorderColor #2D2D2D
    BackgroundColor #FFFFFF
    FontColor #000000
}

skinparam participant {
    BorderColor #2D2D2D
    BackgroundColor #FFFFFF
    FontColor #000000
    FontSize 11
}

skinparam sequence {
    ArrowColor #2D2D2D
    LifeLineColor #2D2D2D
    LifeLineBorderColor #2D2D2D
    GroupBorderColor #2D2D2D
    GroupHeaderFontColor #000000
    GroupBackgroundColor transparent
}

actor "Pengguna\\n(Dokter)" as User
participant "Frontend\\n(DoctorProfile.tsx)" as FE
participant "Profile Service\\n(profile.ts)" as PS
participant "Backend API\\n(Flask)" as BE
participant "Supabase\\n(Database & Auth)" as SB

== Pemuatan Halaman & Data Profil ==

User -> FE : Akses halaman /profile
activate FE

FE -> PS : fetchDoctorProfile(user)
activate PS
PS -> SB : SELECT * FROM doctor_profiles\\nWHERE user_id = user.id
activate SB

alt Data profil ditemukan di database
    SB --> PS : Data profil dari tabel doctor_profiles
else Data profil belum ada di tabel (Fallback)
    SB --> PS : Data kosong / error
    PS -> PS : Gunakan user.user_metadata.doctor_profile\\nsebagai data awal
end
deactivate SB

PS --> FE : Data DoctorProfileData
deactivate PS

FE -> BE : GET /api/history (Bearer Token)
activate BE
BE -> SB : Query riwayat analisis milik user
activate SB
SB --> BE : Data riwayat analisis
deactivate SB
BE --> FE : JSON daftar riwayat analisis
deactivate BE

FE -> FE : computeStats() & calculateCompleteness()
FE --> User : Tampilkan halaman profil, ringkasan statistik,\\n& 5 tab detail profil
deactivate FE

== Pengeditan & Penyimpanan Profil ==

opt Pengguna memilih edit profil
    User -> FE : Klik tombol "Edit Profile"
    activate FE
    FE --> User : Tampilkan modal formulir edit (5 tab)
    deactivate FE

    alt Pengguna membatalkan perubahan
        User -> FE : Klik tombol "Cancel" / tutup modal
        activate FE
        FE --> User : Tutup modal formulir tanpa menyimpan
        deactivate FE

    else Pengguna menyimpan perubahan
        User -> FE : Ubah data & klik tombol "Save Changes"
        activate FE
        FE -> PS : saveDoctorProfile(user, editFormData)
        activate PS

        PS -> PS : validateProfileData(data)

        alt Validasi formulir gagal
            PS --> FE : { error: pesan validasi }
            FE --> User : Tampilkan notifikasi error validasi pada modal
        else Validasi formulir berhasil
            PS -> SB : UPSERT INTO doctor_profiles\\n(data profil, onConflict: user_id)
            activate SB
            SB --> PS : Status hasil upsert
            deactivate SB

            PS -> SB : supabase.auth.updateUser(\\n{ data: { full_name, doctor_profile } })
            activate SB
            SB --> PS : Status pembaruan metadata
            deactivate SB

            alt Penyimpanan berhasil
                PS --> FE : { data: sanitizedProfile }
                FE -> FE : setProfile(data) & hitung kelengkapan
                FE --> User : Tutup modal & tampilkan notifikasi sukses
            else Penyimpanan gagal
                PS --> FE : { error: "Gagal menyimpan profil" }
                FE --> User : Tampilkan notifikasi gagal menyimpan pada modal
            end
        end
        deactivate PS
        deactivate FE
    end
end

@enduml`;

import("@plantuml/core").then(async ({ renderToString }) => {
  renderToString(puml.trim().split("\n"), (svg) => {
    fs.writeFileSync("references/bab 4/sequence_diagram_doctor_profile.svg", svg, "utf8");
    console.log("Wrote references/bab 4/sequence_diagram_doctor_profile.svg");
  }, (err) => {
    console.error("PlantUML ERROR:", err);
  });
}).catch(err => console.error("Import ERROR:", err));
