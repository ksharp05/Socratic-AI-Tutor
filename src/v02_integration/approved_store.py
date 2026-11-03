"""Load a server-pinned, reviewed-example projection; never read raw Directions data."""
import hashlib,json,re
from pathlib import Path
from .audit import load_json,require

MAX_EXAMPLE_BYTES=2_000_000

def load_approved_projection(directory,*,expected_manifest_sha256,policy_id):
 require(isinstance(policy_id,str) and bool(policy_id.strip()),'Explicit policy ID required')
 directory=Path(directory)
 require(directory.is_dir() and not directory.is_symlink(),'Missing/linked approved projection')
 require({p.name for p in directory.iterdir()}=={'examples.jsonl','MANIFEST.json'},'Approved projection allowlist failed')
 require(all(not p.is_symlink() and p.is_file() for p in directory.iterdir()),'Linked/nonfile projection member')
 require((directory/'MANIFEST.json').stat().st_size<=256_000,'Approval manifest exceeds runtime bound')
 manifest_bytes=(directory/'MANIFEST.json').read_bytes()
 require(isinstance(expected_manifest_sha256,str) and hashlib.sha256(manifest_bytes).hexdigest()==expected_manifest_sha256,'Unpinned/stale approved manifest')
 m=load_json(manifest_bytes.decode('utf-8-sig'))
 require(set(m)=={'records','file','sha256','policies','review_evidence_sha256','teaching_permissions_unchanged'},'Unknown approval manifest fields')
 require(m['file']=='examples.jsonl' and m['teaching_permissions_unchanged'] is True and m['policies']==[policy_id],'Policy/version or file drift')
 require(isinstance(m['review_evidence_sha256'],list) and all(isinstance(v,str) and re.fullmatch(r'[0-9a-f]{64}',v) for v in m['review_evidence_sha256']),'Invalid review evidence hashes')
 require((directory/'examples.jsonl').stat().st_size<=MAX_EXAMPLE_BYTES,'Approved examples exceed runtime bound')
 raw=(directory/'examples.jsonl').read_bytes()
 require(hashlib.sha256(raw).hexdigest()==m['sha256'],'Approved example content drift')
 rows=[load_json(s) for s in raw.decode('utf-8-sig').splitlines() if s.strip()]
 require(type(m['records']) is int and len(rows)==m['records']==len(m['review_evidence_sha256']),'Approval/row count mismatch')
 require(len({r.get('example_id') for r in rows})==len(rows),'Duplicate approved example ID')
 for row in rows:
  require(set(row)=={'example_id','chapter','messages'} and row['chapter'] in {'quadratics','ap','trigonometry'},'Private/unknown example fields')
  require(isinstance(row['messages'],list) and 2<=len(row['messages'])<=40,'Invalid example message count')
  for i,message in enumerate(row['messages']):
   require(set(message)=={'role','text'} and message['role']==('student' if i%2==0 else 'tutor') and isinstance(message['text'],str) and 0<len(message['text'])<=4000,'Invalid reviewed message')
 return rows
