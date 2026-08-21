#!/usr/bin/env python3
"""
build_plugin.py  –  Compilador do Plugin Blender Animations para Roblox Studio (.rbxmx)
Uso: python build_plugin.py
"""

import json
import os
import sys
from xml.sax.saxutils import escape
import uuid

# Diretórios
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SOURCEMAP_FILE = os.path.join(PROJECT_ROOT, "sourcemap.json")
LOCAL_OUT_FILE = os.path.join(PROJECT_ROOT, "BlenderAnimations_Decals.rbxmx")

# Pasta de plugins do Roblox Studio do usuário atual
ROBLOX_LOCAL_PLUGINS = os.path.expandvars(r"%LOCALAPPDATA%\Roblox\Plugins\BlenderAnimations_Decals.rbxmx")
INSTALLED_STORE_PLUGIN_DIR = os.path.expandvars(r"%LOCALAPPDATA%\Roblox\5299229453\InstalledPlugins\16708835782\2178722573530")

SCRIPT_CLASSES = {"Script", "LocalScript", "ModuleScript"}

def make_ref() -> str:
    return "RBX" + uuid.uuid4().hex.upper()[:12]

def xml_escape(s: str) -> str:
    return escape(s, {'"': "&quot;", "'": "&apos;"})

def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as e:
        print(f"  [WARN] Nao foi possivel ler {path}: {e}")
        return ""

def pick_source_file(file_paths: list[str]) -> str | None:
    for fp in file_paths:
        if fp.endswith(".lua"):
            return os.path.join(PROJECT_ROOT, fp.replace("/", os.sep))
    return None

def serialise_node(node: dict, depth: int) -> list[str]:
    indent = "\t" * depth
    lines = []

    class_name = node.get("className", "Folder")
    name = node.get("name", "Unknown")
    file_paths = node.get("filePaths", [])
    children = node.get("children", [])
    referent = make_ref()

    lines.append(f'{indent}<Item class="{xml_escape(class_name)}" referent="{referent}">')
    lines.append(f'{indent}\t<Properties>')
    lines.append(f'{indent}\t\t<string name="Name">{xml_escape(name)}</string>')

    if class_name in SCRIPT_CLASSES:
        src_path = pick_source_file(file_paths)
        if src_path and os.path.isfile(src_path):
            source = read_file(src_path)
        else:
            source = ""
        lines.append(f'{indent}\t\t<ProtectedString name="Source"><![CDATA[{source}]]></ProtectedString>')

        if class_name == "Script":
            lines.append(f'{indent}\t\t<bool name="Disabled">false</bool>')

    lines.append(f'{indent}\t</Properties>')

    for child in children:
        lines.extend(serialise_node(child, depth + 1))

    lines.append(f'{indent}</Item>')
    return lines

def build_rbxmx(nodes_to_compile: list[dict]) -> str:
    lines = [
        '<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime"',
        '        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
        '        xsi:noNamespaceSchemaLocation="https://raw.githubusercontent.com/MaximumADHD/Roblox-File-Format/main/Roblox.xsd"',
        '        version="4">',
        '\t<External>null</External>',
        '\t<External>nil</External>',
    ]
    for node in nodes_to_compile:
        lines.extend(serialise_node(node, depth=1))
    lines.append('</roblox>')
    return "\n".join(lines)

def main():
    print("=" * 60)
    print("   Compilador do Plugin Blender Animations (.rbxmx)")
    print("=" * 60)

    if not os.path.isfile(SOURCEMAP_FILE):
        print(f"[ERRO] sourcemap.json nao encontrado em: {SOURCEMAP_FILE}")
        sys.exit(1)

    with open(SOURCEMAP_FILE, "r", encoding="utf-8") as f:
        sourcemap = json.load(f)

    top_nodes = []
    for root_child in sourcemap.get("children", []):
        if root_child.get("name") != "ServerScriptService":
            continue
        for sss_child in root_child.get("children", []):
            if sss_child.get("name") == "BlenderAnimationsInternal":
                for item in sss_child.get("children", []):
                    top_nodes.append(item)
                break

    if not top_nodes:
        print("[ERRO] Nenhum no encontrado no sourcemap.json.")
        sys.exit(1)

    print("[*] Gerando XML do plugin...")
    wrapper = {
        "name": "BlenderAnimationsInternal",
        "className": "Folder",
        "filePaths": [],
        "children": top_nodes,
    }
    xml = build_rbxmx([wrapper])

    # 1. Salva na pasta do projeto
    with open(LOCAL_OUT_FILE, "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"[OK] Salvo no projeto: {LOCAL_OUT_FILE} ({os.path.getsize(LOCAL_OUT_FILE)/1024:.1f} KB)")

    # 2. Salva na pasta de Plugins do Roblox Studio
    try:
        os.makedirs(os.path.dirname(ROBLOX_LOCAL_PLUGINS), exist_ok=True)
        with open(ROBLOX_LOCAL_PLUGINS, "w", encoding="utf-8") as f:
            f.write(xml)
        print(f"[OK] Instalado na pasta Plugins do Studio: {ROBLOX_LOCAL_PLUGINS}")
    except Exception as e:
        print(f"[!] Nao foi possivel copiar para a pasta Plugins: {e}")

    print("=" * 60)
    print("   [SUCESSO] Compilacao concluida com sucesso!")
    print("=" * 60)


if __name__ == "__main__":
    main()
