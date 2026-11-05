import io
from pathlib import Path

import pandas as pd
from flask import Blueprint, jsonify, request, send_file

from .models import UploadedFile
from . import db

bp = Blueprint("api", __name__)

UPLOAD_FOLDER = Path("uploads")


def _allowed(filename: str) -> bool:
    return Path(filename).suffix.lower() in {".csv", ".xlsx", ".xls"}


def _load_dataframe(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    return pd.read_excel(path)


@bp.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if file is None or file.filename == "":
        return jsonify({"error": "Файл не передан (поле 'file')"}), 400
    if not _allowed(file.filename):
        return jsonify({"error": "Разрешены только CSV и Excel"}), 400

    UPLOAD_FOLDER.mkdir(exist_ok=True)
    saved = UPLOAD_FOLDER / file.filename
    file.save(saved)

    record = UploadedFile(filename=file.filename, path=str(saved))
    db.session.add(record)
    db.session.commit()

    return jsonify({"file_id": record.id, "filename": record.filename}), 201


@bp.route("/data/stats", methods=["GET"])
def stats():
    file_id = request.args.get("file_id", type=int)
    if file_id is None:
        return jsonify({"error": "Укажите file_id"}), 400

    record = db.session.get(UploadedFile, file_id)
    if record is None:
        return jsonify({"error": "Файл не найден"}), 404

    df = _load_dataframe(Path(record.path))
    numeric = df.select_dtypes("number")
    result = {
        col: {
            "mean": float(numeric[col].mean()),
            "median": float(numeric[col].median()),
        }
        for col in numeric.columns
    }
    corr = numeric.corr(numeric_only=True).fillna(0).round(3).to_dict()
    return jsonify({"columns": result, "correlation": corr})


@bp.route("/data/clean", methods=["GET"])
def clean():
    file_id = request.args.get("file_id", type=int)
    strategy = request.args.get("strategy", "median")
    if file_id is None:
        return jsonify({"error": "Укажите file_id"}), 400

    record = db.session.get(UploadedFile, file_id)
    if record is None:
        return jsonify({"error": "Файл не найден"}), 404

    df = _load_dataframe(Path(record.path))
    numeric = df.select_dtypes("number")
    filled = numeric.fillna(numeric.median() if strategy == "median" else numeric.mean())
    removed = int(len(df) - len(df.dropna()))
    return jsonify({"strategy": strategy, "rows_before": len(df), "dropped_rows": removed,
                    "preview": filled.head(10).to_dict(orient="records")})


@bp.route("/data/plot", methods=["GET"])
def plot():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    file_id = request.args.get("file_id", type=int)
    plot_type = request.args.get("type", "histogram")
    columns = request.args.get("columns", "")
    if file_id is None:
        return jsonify({"error": "Укажите file_id"}), 400

    record = db.session.get(UploadedFile, file_id)
    if record is None:
        return jsonify({"error": "Файл не найден"}), 404

    df = _load_dataframe(Path(record.path))
    cols = [c for c in columns.split(",") if c in df.columns]
    if not cols:
        return jsonify({"error": "Не найдено ни одной указанной колонки"}), 400

    fig, ax = plt.subplots(figsize=(8, 5))
    if plot_type == "histogram":
        for col in cols:
            ax.hist(df[col].dropna(), bins=30, alpha=0.5, label=col)
        ax.legend()
    else:
        for col in cols:
            ax.plot(df.index, df[col], label=col)
        ax.legend()
    ax.set_title(f"{plot_type}: {', '.join(cols)}")

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")
