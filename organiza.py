#!/usr/bin/env python3
"""
Organizador automático de arquivos.

Move os arquivos de uma pasta para subpastas, de acordo com a extensão.

Exemplos:
    python organizador.py ~/Downloads --simular     # só mostra o que faria
    python organizador.py ~/Downloads               # organiza de verdade
    python organizador.py ~/Downloads --vigiar      # fica monitorando (pip install watchdog)
"""

import argparse
import shutil
import time
from pathlib import Path

CATEGORIAS = {
    "Imagens": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".heic"},
    "Documentos": {".pdf", ".doc", ".docx", ".txt", ".odt", ".rtf", ".md"},
    "Planilhas": {".xls", ".xlsx", ".csv", ".ods"},
    "Apresentacoes": {".ppt", ".pptx", ".odp"},
    "Videos": {".mp4", ".mkv", ".avi", ".mov", ".wmv"},
    "Audios": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"},
    "Compactados": {".zip", ".rar", ".7z", ".tar", ".gz"},
    "Codigo": {".py", ".js", ".html", ".css", ".java", ".c", ".cpp", ".json", ".sql"},
    "Executaveis": {".exe", ".msi", ".deb", ".dmg", ".apk"},
}
OUTROS = "Outros"


def categoria_do_arquivo(arquivo: Path) -> str:
    ext = arquivo.suffix.lower()
    for nome, extensoes in CATEGORIAS.items():
        if ext in extensoes:
            return nome
    return OUTROS


def destino_sem_conflito(destino: Path) -> Path:
    """Se já existir um arquivo com o mesmo nome, adiciona (1), (2)..."""
    if not destino.exists():
        return destino
    contador = 1
    while True:
        novo = destino.with_name(f"{destino.stem} ({contador}){destino.suffix}")
        if not novo.exists():
            return novo
        contador += 1


def organizar_arquivo(arquivo: Path, pasta_base: Path, simular: bool = False) -> None:
    if not arquivo.is_file() or arquivo.name.startswith("."):
        return
    if arquivo.resolve() == Path(__file__).resolve():
        return  # não move o próprio script

    pasta_destino = pasta_base / categoria_do_arquivo(arquivo)
    destino = destino_sem_conflito(pasta_destino / arquivo.name)

    print(f"{'[SIMULAÇÃO] ' if simular else ''}{arquivo.name}  ->  {destino.relative_to(pasta_base)}")
    if not simular:
        pasta_destino.mkdir(exist_ok=True)
        shutil.move(str(arquivo), str(destino))


def organizar_pasta(pasta: Path, simular: bool = False) -> int:
    arquivos = [a for a in pasta.iterdir() if a.is_file()]
    for arquivo in arquivos:
        organizar_arquivo(arquivo, pasta, simular)
    return len(arquivos)


def arquivo_pronto(arquivo: Path, espera: float = 1.0) -> bool:
    """Evita mover arquivos ainda em download (tamanho ainda mudando)."""
    try:
        tamanho = arquivo.stat().st_size
        time.sleep(espera)
        return tamanho == arquivo.stat().st_size
    except FileNotFoundError:
        return False


def vigiar_pasta(pasta: Path) -> None:
    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:
        raise SystemExit("Para o modo --vigiar instale: pip install watchdog")

    class Handler(FileSystemEventHandler):
        def on_created(self, event):
            if event.is_directory:
                return
            arquivo = Path(event.src_path)
            # ignora arquivos temporários de download
            if arquivo.suffix.lower() in {".crdownload", ".part", ".tmp"}:
                return
            if arquivo.parent == pasta and arquivo_pronto(arquivo):
                organizar_arquivo(arquivo, pasta)

    observer = Observer()
    observer.schedule(Handler(), str(pasta), recursive=False)
    observer.start()
    print(f"Monitorando {pasta} ... (Ctrl+C para sair)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def main() -> None:
    parser = argparse.ArgumentParser(description="Organiza arquivos por tipo.")
    parser.add_argument("pasta", type=Path, help="Pasta a ser organizada")
    parser.add_argument("--simular", action="store_true", help="Mostra o que seria feito, sem mover nada")
    parser.add_argument("--vigiar", action="store_true", help="Continua monitorando a pasta")
    args = parser.parse_args()

    pasta = args.pasta.expanduser().resolve()
    if not pasta.is_dir():
        raise SystemExit(f"Pasta não encontrada: {pasta}")

    total = organizar_pasta(pasta, args.simular)
    print(f"\n{total} arquivo(s) processado(s).")

    if args.vigiar and not args.simular:
        vigiar_pasta(pasta)


if __name__ == "__main__":
    main()
