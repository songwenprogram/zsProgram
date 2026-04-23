"""
TXT 文本处理脚本 - 环境测试专用
功能：自动生成测试文件 -> 读取处理 -> 输出新文件
目的：验证 Python 环境是否正常，文件读写权限是否具备
"""

import os
import sys

def create_test_file(filename="test_input.txt"):
    """创建一个包含示例文本的测试文件"""
    sample_text = """Hello, this is a test file.
It contains multiple lines.
We will count words, lines, and replace 'test' with 'demo'.
This is the last line."""
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(sample_text)
        print(f"✅ 测试文件已创建: {filename}")
        return True
    except Exception as e:
        print(f"❌ 创建测试文件失败: {e}")
        return False

def process_text_file(input_file, output_file):
    """处理文本文件的核心逻辑"""
    try:
        # 1. 读取文件
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.splitlines()
        
        # 2. 统计信息
        line_count = len(lines)
        word_count = len(content.split())
        
        # 3. 文本替换 (示例：将 'test' 替换为 'demo')
        processed_content = content.replace('test', 'demo')
        
        # 4. 构建处理报告
        report = f"""--- 文本处理报告 ---
输入文件: {input_file}
总行数: {line_count}
总单词数: {word_count}
已将 'test' 替换为 'demo'
处理时间: {__import__('datetime').datetime.now()}
"""
        
        # 5. 写入输出文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=== 处理后的文本内容 ===\n")
            f.write(processed_content)
            f.write("\n\n")
            f.write(report)
        
        print(f"✅ 处理完成，结果已保存至: {output_file}")
        print(f"📊 统计: 共 {line_count} 行, {word_count} 个单词")
        return True
        
    except FileNotFoundError:
        print(f"❌ 错误: 找不到输入文件 '{input_file}'")
        return False
    except PermissionError:
        print(f"❌ 错误: 没有读写文件的权限")
        return False
    except Exception as e:
        print(f"❌ 处理过程中发生未知错误: {e}")
        return False

def main():
    """主函数：串联整个测试流程"""
    print("=" * 40)
    print("🐍 Python 文本处理环境测试")
    print(f"Python 版本: {sys.version}")
    print(f"当前工作目录: {os.getcwd()}")
    print("=" * 40)
    
    # 定义文件名
    test_file = "test_input.txt"
    result_file = "test_output.txt"
    
    # 步骤1: 创建测试文件
    if not create_test_file(test_file):
        sys.exit(1)  # 创建失败则退出
    
    # 步骤2: 处理文件并生成输出
    if process_text_file(test_file, result_file):
        print("\n🎉 环境测试通过！Python 可以正常处理 TXT 文件。")
    else:
        print("\n⚠️ 测试未完全通过，请检查上方错误信息。")

if __name__ == "__main__":
    main()