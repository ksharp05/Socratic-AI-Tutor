from __future__ import annotations
import argparse,json,shutil,sqlite3,os
from pathlib import Path
from .bootstrap import bootstrap
from .knowledge import DatasetRegistry,import_jsonl,SAFE_ID,database
from ncert_pipeline.build import insert_passage


def main():
    code_root=Path(__file__).resolve().parents[2]
    root=Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE',code_root)).resolve()
    p=argparse.ArgumentParser(description='Socrates modular local beta')
    p.add_argument('--config',type=Path,default=code_root/'config/beta/local.json')
    sub=p.add_subparsers(dest='command',required=True)
    serve=sub.add_parser('serve');serve.add_argument('--live',action='store_true');serve.add_argument('--port',type=int);serve.add_argument('--max-live-calls',type=int)
    sub.add_parser('init');sub.add_parser('datasets')
    a=sub.add_parser('activate');a.add_argument('dataset_id')
    q=sub.add_parser('import');q.add_argument('--file',type=Path,required=True);q.add_argument('--id',required=True);q.add_argument('--title',required=True);q.add_argument('--base');q.add_argument('--activate',action='store_true')
    q=sub.add_parser('register-index');q.add_argument('--file',type=Path,required=True);q.add_argument('--id',required=True);q.add_argument('--title',required=True);q.add_argument('--activate',action='store_true')
    args=p.parse_args()
    if not args.config.exists():args.config=code_root/'config/beta/local.example.json'
    settings=json.loads(args.config.read_text(encoding='utf-8-sig'))
    app_root=Path(settings['app_root']);settings['app_root']=str(app_root if app_root.is_absolute() else (code_root/app_root).resolve())
    data=Path(settings.get('data_directory','Directions/beta_data'));data=data if data.is_absolute() else root/data
    registry=bootstrap(root,Path(settings['app_root']),data)
    if args.command in ('init','datasets'):print(json.dumps(registry.public(),indent=2));return
    if args.command=='activate':registry.activate(args.dataset_id);print('Active dataset:',args.dataset_id);return
    if args.command=='register-index':
        print(json.dumps(registry.register(args.id,args.file,title=args.title,activate=args.activate),indent=2));return
    if args.command=='import':
        if not SAFE_ID.fullmatch(args.id):raise ValueError('Invalid dataset id')
        folder=data/'datasets'/args.id
        if folder.exists():raise ValueError('Dataset version directory already exists; choose a new id')
        folder.mkdir(parents=True)
        additions=folder/'import.sqlite';count=import_jsonl(args.file,additions)
        target=additions
        if args.base:
            base=registry.knowledge(args.base);target=folder/'knowledge.sqlite';shutil.copy2(base.path,target)
            with database(target) as c,database(additions) as added:
                added.row_factory=sqlite3.Row
                for row in added.execute('SELECT * FROM passages'):
                    row=dict(row);grades=[g[0] for g in added.execute('SELECT grade FROM scopes WHERE passage_id=?',(row['id'],))]
                    insert_passage(c,row,grades)
        entry=registry.register(args.id,target,title=args.title,activate=args.activate,provenance={'adapter':'passage-jsonl-v1','added':count,'base':args.base})
        print(json.dumps(entry,indent=2));return
    if args.max_live_calls is not None:settings['max_live_calls']=args.max_live_calls
    import uvicorn
    from .api import create_app
    app=create_app(settings,live=args.live)
    mode='live language model' if args.live else 'offline source-backed fallback'
    port=args.port or settings.get('port',8770)
    print(f'Socrates beta: http://127.0.0.1:{port} — {mode}',flush=True)
    uvicorn.run(app,host='127.0.0.1',port=port,log_level='warning')

if __name__=='__main__':main()
