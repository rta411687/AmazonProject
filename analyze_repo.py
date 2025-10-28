# analyze_repo.py
import os, json, re
ROOT = os.getcwd()

def list_apps():
    apps=[]
    for d in os.listdir(ROOT):
        p=os.path.join(ROOT,d)
        if os.path.isdir(p) and (os.path.exists(os.path.join(p,'models.py')) or os.path.exists(os.path.join(p,'views.py'))):
            apps.append(d)
    return apps

def find_settings():
    for dirpath,_,files in os.walk(ROOT):
        if 'settings.py' in files and os.path.basename(dirpath) == 'AmazonProject':
            return os.path.join(dirpath,'settings.py')
        if 'settings.py' in files:
            return os.path.join(dirpath,'settings.py')
    return None

def read_installed_apps(settings_path):
    if not settings_path: return []
    try:
        text=open(settings_path,encoding='utf-8').read()
        m=re.search(r'INSTALLED_APPS\s*=\s*\[([^\]]+)\]',text,re.S) or re.search(r'INSTALLED_APPS\s*=\s*\(([^\)]+)\)',text,re.S)
        if not m: return []
        return re.findall(r'["\']([^"\']+)["\']', m.group(1))
    except Exception:
        return []

py_files=[]
for dirpath,_,filenames in os.walk(ROOT):
    for f in filenames:
        if f.endswith('.py'):
            py_files.append(os.path.join(dirpath,f))

settings_path=find_settings()
summary = {
  "root": ROOT,
  "top_level_apps": list_apps(),
  "python_files": len(py_files),
  "has_db_sqlite": os.path.exists(os.path.join(ROOT,'db.sqlite3')),
  "settings_path": settings_path,
  "installed_apps_sample": read_installed_apps(settings_path)[:30],
  "has_manage_py": os.path.exists(os.path.join(ROOT,'manage.py'))
}
print(json.dumps(summary))