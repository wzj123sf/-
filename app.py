from flask import Flask, render_template, request, send_file, redirect, url_for
import json
import os
import shutil
from utils.docx_generator import create_docx
from utils.pdf_generator import create_pdf
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import os
import whisper
import torch
from datetime import datetime
from werkzeug.utils import secure_filename
app = Flask(__name__)
app.config.update(
    UPLOAD_FOLDER=os.path.abspath('temp/audio'),
    MODEL_FOLDER=os.path.abspath('tempmodels'),  # 确保绝对路径
    SECRET_KEY='your_secret_key_here',
    ALLOWED_EXTENSIONS={'wav', 'mp3', 'ogg', 'flac', 'webm'},
    MAX_CONTENT_LENGTH=100 * 1024 * 1024
)
# 创建必要目录
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['MODEL_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def load_data():
    with open('data/example.json', 'r', encoding='utf-8') as f:
        return json.load(f)
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('请选择音频文件')
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash('未选择文件')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        # 生成带时间戳的安全文件名
        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        return redirect(url_for('transcribe', filename=filename))

    flash('不支持的文件类型')
    return redirect(url_for('index'))


def load_whisper_model(model_size='base'):
    """加载模型，优先从本地tempmodels加载"""
    try:
        # 模型存储路径：tempmodels/{model_size}/
        model_path = os.path.join(app.config['MODEL_FOLDER'], model_size)

        # 如果本地不存在则自动下载
        if not os.path.exists(model_path):
            os.makedirs(model_path, exist_ok=True)
            print(f"正在下载模型到：{model_path}")

        # 加载模型（自动处理下载逻辑）
        model = whisper.load_model(
            name=model_size,
            download_root=app.config['MODEL_FOLDER'],  # 关键配置
            device="cuda" if torch.cuda.is_available() else "cpu"
        )
        return model
    except Exception as e:
        raise RuntimeError(f"模型加载失败：{str(e)}")


@app.route('/transcribe/<filename>')
def transcribe(filename):
    # 获取本地可用模型
    existing_models = []
    model_dir = app.config['MODEL_FOLDER']
    if os.path.exists(model_dir):
        existing_models = [d for d in os.listdir(model_dir)
                           if os.path.isdir(os.path.join(model_dir, d))
                           and d in whisper.available_models()]

    return render_template('transcribe.html',
                           filename=filename,
                           existing_models=existing_models,
                           all_models=whisper.available_models())


@app.route('/process', methods=['POST'])
def process_audio():
    filename = request.form['filename']
    model_size = request.form.get('model_size', 'base')
    language = request.form.get('language', 'zh')

    try:
        # 验证文件存在
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(audio_path):
            raise FileNotFoundError("音频文件不存在")

        # 加载模型
        model = load_whisper_model(model_size)

        # 执行转录
        result = model.transcribe(
            audio=audio_path,
            language=language if language != 'auto' else None,
            fp16=torch.cuda.is_available()
        )

        # 保存结果
        result_text = result['text']
        result_filename = f"result_{filename.split('_', 1)[1].rsplit('.', 1)[0]}.txt"
        with open(os.path.join(app.config['UPLOAD_FOLDER'], result_filename),
                  'w', encoding='utf-8') as f:
            f.write(result_text)

        return render_template('result.html',
                               original_file=filename,
                               result_text=result_text,
                               download_file=result_filename)

    except Exception as e:
        flash(f'处理失败: {str(e)}')
        return redirect(url_for('transcribe', filename=filename))


@app.route('/download/<filename>')
def download_result(filename):
    return send_from_directory(
        directory=app.config['UPLOAD_FOLDER'],
        path=filename,
        as_attachment=True
    )
@app.route('/meeting')
def show_preview():
    return render_template('meeting.html')
@app.route('/exchange')
def show_exchange():
    return render_template('exchange.html')

@app.route('/report')
def show_report():
    data = load_data()
    return render_template('report.html', data=data)


@app.route('/export', methods=['POST'])
def export_report():
    data = load_data()
    format_type = request.form['format']

    if format_type == 'docx':
        filename = create_docx(data)
        return send_file(filename, as_attachment=True)
    elif format_type == 'pdf':
        filename = create_pdf(data)
        return send_file(filename, as_attachment=True)
    else:
        return "Unsupported format", 400



if __name__ == '__main__':
    app.run(debug=True)