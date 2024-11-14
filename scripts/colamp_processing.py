import subprocess
import scripts.color as color # 输出信息高亮
import os
import shutil

# 设置路径
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 获取根目录路径
upload_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads\\')  # 获取uploads文件夹路径
colmap_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'COLMAP\\')  # 获取COLMAP文件夹路径
colmap_bin = os.path.join(colmap_path, 'bin', 'colmap.exe')  # colmap.exe的路径
lib_path = os.path.join(colmap_path, 'lib\\')  # lib文件夹路径
script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '')  # scripts文件夹路径
ffmpeg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ffmpeg\\') # ffmpeg文件夹路径

# 设置环境变量
env = os.environ.copy()
env['QT_PLUGIN_PATH'] = os.path.join(lib_path, 'plugins')
env['PATH'] = f"{env['QT_PLUGIN_PATH']};{env['PATH']}"

# 移动所有文件和文件夹
def move_all_files_and_dirs(src_folder, dest_folder):
    if os.path.isdir(src_folder):
        os.makedirs(dest_folder, exist_ok=True)
        for item in os.listdir(src_folder):
            src_item = os.path.join(src_folder, item) # 获取源文件的完整路径
            dest_item = os.path.join(dest_folder, item) # 获取目标文件的完整路径
            if os.path.isdir(src_item):
                shutil.move(src_item, dest_item)# 如果是文件夹，递归移动文件夹
            else:
                shutil.move(src_item, dest_item)# 如果是文件，直接移动文件
    else:
        if os.path.exists(src_folder):
            shutil.move(src_folder, dest_folder)

    print(color.COLOR_BLUE(f"All contents from {src_folder} have been moved to {dest_folder}"))
        
# 定义预处理的命令
def run_colmap(command, *args):
    cmd = [colmap_bin, command] + list(args)
    try:
        subprocess.run(cmd, check=True, env=env)
        print(f"Command '{' '.join(cmd)}' executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        return False
    return True

# 使用colmap进行图像预处理
def process_images(image_path, db_path):
    # 1. 特征提取
    run_colmap("feature_extractor", "--database_path", db_path, "--image_path", image_path)
    # 2. 匹配特征
    run_colmap("exhaustive_matcher", "--database_path", db_path)
    # 3. 重建3D
    run_colmap("mapper", "--database_path", db_path, "--image_path", image_path, "--output_path", os.path.join(colmap_path, "output"))
    # 4. 获取相机与图像信息并生成输出文件
    run_colmap("model_converter", "--input_path", os.path.join(colmap_path, "output", "0"), "--output_path", os.path.join(colmap_path, "output"), "--output_type", "TXT")
    # 生成 db 文件和 transform.json
    print("Image processing complete.")

# colmap2nerf
def process_video2nerf(file_name, file_path):
    
    print(color.COLOR_GREEN(f"[+] File Name: {file_name}"))
    print(color.COLOR_GREEN(f"[+] File Path: {file_path}"))
    
    transfrom_path = os.path.join(upload_path, file_path, '' )   # 生成的transform.json文件路径
    file_full_path = os.path.join(upload_path, file_path , file_name) # 视频文件路径
    ffmpeg_out_path = os.path.join(upload_path, file_path, '') # ffmpeg输出路径
    
    # ----------------------------------------------------------------------
    print(color.COLOR_CYAN(f"[+] File Full Path: {file_full_path}"))
    print(color.COLOR_CYAN(f"[+] TransformPath: {transfrom_path}"))
    print(color.COLOR_CYAN(f"[+] FFMPEG Out Path: {ffmpeg_out_path}"))
    # ----------------------------------------------------------------------
    
    # 运行命令
    command = f"python {script_path}colmap2nerf.py --video_in {file_full_path} --video_fps 4 --output {transfrom_path} --run_colmap"
    print(color.COLOR_PURPLE(f"[+] Running command: {command}"))
    # 获取命令执行完成后的输出
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    output = result.stdout
    err = result.stderr
    # 写日志
    with open(transfrom_path+"log.txt", "w+") as f:
        f.write(output)
        f.write('\n\n---------------------------------------------------------------------------\n\n')
        f.write(err)
    # print(color.COLOR_YELLOW(f"[+] OutputRes: {output}"))
    # print(color.COLOR_RED(f"[+] ErrorRes: {err}"))
    
    # 生成文件移动到上传目录
    # ----------------------------------------------------------------------
    print(color.COLOR_GREEN(f"[+] Move All Files and Dirs: {os.path.join(root_path, 'colmap_sparse', '')}"))
    print(color.COLOR_GREEN(f"[+] Move All Files and Dirs: {os.path.join(root_path, 'colmap_text', '')}"))
    print(color.COLOR_GREEN(f"[+] Move All Files and Dirs: {os.path.join(root_path, 'colmap.db')}"))
    print(color.COLOR_GREEN(f"[+] Move All Files and Dirs: {os.path.join(script_path, 'imgui.ini')}"))
    # ----------------------------------------------------------------------
    move_all_files_and_dirs(os.path.join(root_path, 'colmap_sparse',''), transfrom_path)
    move_all_files_and_dirs(os.path.join(root_path, 'colmap_text'), transfrom_path)
    move_all_files_and_dirs(os.path.join(root_path, 'colmap.db'), transfrom_path)
    move_all_files_and_dirs(os.path.join(root_path, 'imgui.ini'), transfrom_path)
    return output, err
    
    
    
