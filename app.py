import os
import uuid
import sqlite3
import scripts.colamp_processing as colamp_processing # colmap 处理视频
import scripts.color as color # 输出信息高亮
from flask import Flask, request, render_template

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 设置最大文件上传大小为 100MB


def test_path():
    # ---------------------------- 测试 ----------------------------
    print(color.COLOR_CYAN(f"[+] colmap_path: {colamp_processing.colmap_path}"))
    print(color.COLOR_CYAN(f"[+] colmap_bin: {colamp_processing.colmap_bin}"))
    print(color.COLOR_CYAN(f"[+] lib_path: {colamp_processing.lib_path}"))
    print(color.COLOR_CYAN(f"[+] script_path: {colamp_processing.script_path}"))
    print(color.COLOR_CYAN(f"[+] ffmpeg_path: {colamp_processing.ffmpeg_path}"))
    print(color.COLOR_CYAN(f"[+] upload_path: {colamp_processing.upload_path}"))
    # ----------------------------------------------------------------

# 创建保存文件的目录
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 初始化数据库
conn = sqlite3.connect('file_mapping.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS files
             (id INTEGER PRIMARY KEY, original_filename TEXT, new_filename TEXT)''')
conn.commit()
conn.close()


@app.route('/')
def index():
    return render_template("Upload.html")


@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        if 'video' not in request.files:
            return 'No folder part'
        folder = request.files.getlist('video')
        try:
            conn = sqlite3.connect('file_mapping.db')
            # noinspection PyShadowingNames
            c = conn.cursor()
            for file in folder:
                if file.filename == '':
                    return '没有选择文件'
                if file:
                    original_filename = file.filename.split(".")[0]
                    appended_filename = file.filename.split(".")[1]
                    print(color.COLOR_GREEN(f"[+] Original Filename: {original_filename}"))
                    # 查询数据库，检查文件名是否已经存在
                    c.execute("SELECT id FROM files WHERE original_filename=?", (original_filename,))
                    existing_file = c.fetchone()
                    if existing_file:
                        continue
                    else:
                        # 生成唯一的文件名
                        new_filename = str(uuid.uuid4())
                        print(color.COLOR_GREEN(f"[+] UUID: {new_filename}"))
                        # 创建新目录，并确保目录存在
                        new_folder_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                        os.makedirs(new_folder_path, exist_ok=True)
                        
                        # 保存文件到新创建的目录
                        file_path = os.path.join(new_folder_path, original_filename+"."+appended_filename)
                        file.save(file_path)
                        
                        # 存储原始文件名和新文件名的关联关系到数据库
                        c.execute("INSERT INTO files (original_filename, new_filename) VALUES (?, ?)",
                                  (original_filename+ '.' +appended_filename, new_filename))
            conn.commit()
                    
            return '文件上传完成'
        except Exception as e:
            return '文件上载过程中出错: {}'.format(str(e))
        finally:
            conn.close()
    else:
        return '请求方法不允许'


@app.route('/list_files', methods=['GET'])
def list_files():
    conn = sqlite3.connect('file_mapping.db')
    c = conn.cursor()
    c.execute("SELECT original_filename, new_filename FROM files")
    files = c.fetchall()
    conn.close()
    return render_template('Review.html', files=files)

@app.route('/process2nerf', methods=['GET'])
def process2nerf():
    test_path()
    file_name = request.args.get('file_name')
    file_path = request.args.get('file_path')
    colamp_processing.process_video2nerf(file_name, file_path) # colmap 处理视频
    return '处理完成'
   
@app.route('/render')
def render():
    file_path = request.args.get('file_path')
    command = os.path.join(colamp_processing.root_path, 'instant-ngp.exe ') + os.path.join(colamp_processing.upload_path, file_path) 
    print(color.COLOR_PURPLE(f"[+] Command: {command}"))
    os.system(command)
    return "已结束渲染"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
