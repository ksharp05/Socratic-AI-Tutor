"""Versioned public notes supplement the frozen source pack without rewriting it."""
import hashlib,json
from pathlib import Path

class SupplementedKnowledge:
    def __init__(self,base,notes,digest):
        self.base=base
        self.dataset_id=base.dataset_id
        self.reference_bundle="teaching-notes-v1:"+digest
        self.notes={}
        self.replacements={}
        for note in notes:
            original=base.passage(note["replaces"])
            if original is None:continue
            source="openstax-precalculus-2e-5-4" if note["concept_id"].startswith("tr") else ("openstax-college-algebra-2e-9-2" if note["concept_id"].startswith("ap") else "openstax-college-algebra-2e-2-5")
            passage={**original,**note,"kind":"reference_note","source_id":source,"source_sha256":digest,
                     "page":0,"human_review_status":"pending","approved":0}
            self.notes[note["id"]]=passage
            self.replacements[note["replaces"]]=passage
        # Make the note text searchable through the base index (it replaces the passage after ranking).
        base.extra_text={pid:p.get("title","")+" "+p["text"] for pid,p in self.replacements.items()}
    def __getattr__(self,name):return getattr(self.base,name)
    def passage(self,pid):return self.notes.get(pid) or self.base.passage(pid)
    def search(self,query,scope,limit=3):
        return [self.replacements.get(p["id"],p) for p in self.base.search(query,scope,limit)]

class SupplementedRegistry:
    def __init__(self,base,root):
        self.base=base
        raw=(Path(root)/"content/beta_references/v1/notes.json").read_bytes()
        data=json.loads(raw)
        if data["version"]!="teaching-notes-v1" or data["human_review_status"]!="pending":
            raise ValueError("Unknown reference-note policy")
        self.notes=data["notes"]
        self.digest=hashlib.sha256(raw).hexdigest()
        self.cache={}
        if len({n["id"] for n in self.notes})!=len(self.notes) or len({n["replaces"] for n in self.notes})!=len(self.notes):
            raise ValueError("Duplicate reference note")
        for n in self.notes:
            if (n["id"]!="beta-reference-v1:"+n["concept_id"] or n["replaces"]!="normalized:"+n["concept_id"]
                    or not n["source_url"].startswith("https://openstax.org/books/")
                    or not 40<=len(n["text"])<=1400):
                raise ValueError("Invalid public reference note")
    def __getattr__(self,name):return getattr(self.base,name)
    def public(self):
        return {**self.base.public(),"reference_notes":{"version":"teaching-notes-v1","sha256":self.digest,
                "count":len(self.notes),"human_review_status":"pending","base_pack_unchanged":True}}
    def knowledge(self,dataset_id=None):
        base=self.base.knowledge(dataset_id)
        if base.dataset_id not in self.cache:
            self.cache[base.dataset_id]=SupplementedKnowledge(base,self.notes,self.digest)
        return self.cache[base.dataset_id]
