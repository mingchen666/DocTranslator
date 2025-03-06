import zipfile
import xml.etree.ElementTree as ET
import os
from docx import Document

def read_comments_from_docx(docx_path):
    comments = []
    with zipfile.ZipFile(docx_path, 'r') as docx:
        # 尝试读取批注文件
        with docx.open('word/comments.xml') as comments_file:
            # 解析 XML
            tree = ET.parse(comments_file)
            root = tree.getroot()
            
            # 定义命名空间
            namespace = {'ns0': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            
            # 查找所有批注
            for comment in root.findall('ns0:comment', namespace):
                comment_id = comment.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id')
                author = comment.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}author')
                date = comment.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}date')
                text = ''.join(t.text for p in comment.findall('.//ns0:p', namespace) for r in p.findall('.//ns0:r', namespace) for t in r.findall('.//ns0:t', namespace))
                
                comments.append({
                    'id': comment_id,
                    'author': author,
                    'date': date,
                    'text': text,
                })
            modified_xml = ET.tostring(root, encoding='utf-8', xml_declaration=True).decode('utf-8')
            print("XML 内容:")
            print(modified_xml)
    return comments

def modify_comment_in_docx(docx_path, comment_id, new_text):
    # 创建一个临时文件名，保留原始路径
    temp_docx_path = os.path.join(os.path.dirname(docx_path), 'temp_' + os.path.basename(docx_path))

    # 打开原始 docx 文件
    with zipfile.ZipFile(docx_path, 'r') as docx:
        # 创建一个新的 docx 文件
        with zipfile.ZipFile(temp_docx_path, 'w') as new_docx:
            for item in docx.infolist():
                # 读取每个文件
                with docx.open(item) as file:
                    if item.filename == 'word/comments.xml':
                        # 解析批注 XML
                        tree = ET.parse(file)
                        root = tree.getroot()
                        
                        # 打印原始 XML 内容
                        print("原始 XML 内容:")
                        print(ET.tostring(root, encoding='utf-8', xml_declaration=True).decode('utf-8'))
                        
                        # 定义命名空间
                        namespace = {'ns0': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                        
                        # 查找并修改批注
                        for comment in root.findall('ns0:comment', namespace):
                            if comment.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id') == comment_id:
                                # 清除现有段落
                                for p in list(comment.findall('.//ns0:p', namespace)):
                                    comment.remove(p)  # 从批注中移除段落元素
                                
                                # 创建新的段落
                                new_paragraph = ET.Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p')
                                # 创建新的 run 元素
                                new_run = ET.Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r')
                                # 创建新的 text 元素
                                new_text_elem = ET.Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
                                new_text_elem.text = new_text  # 设置文本内容
                                
                                # 将 text 元素添加到 run 元素中
                                new_run.append(new_text_elem)
                                # 将 run 添加到段落中
                                new_paragraph.append(new_run)
                                # 将新段落添加到批注中
                                comment.append(new_paragraph)
                        
                        # 打印修改后的 XML 内容
                        modified_xml = ET.tostring(root, encoding='utf-8', xml_declaration=True).decode('utf-8')
                        print("修改后的 XML 内容:")
                        print(modified_xml)
                        
                        # 将修改后的 XML 写入新的 docx 文件
                        new_docx.writestr(item.filename, modified_xml)
                    else:
                        # 其他文件直接写入新的 docx 文件
                        new_docx.writestr(item.filename, file.read())

    # 替换原始文件
    os.replace(temp_docx_path, docx_path)

# 示例用法
docx_path = '/Volumes/data/erui/ezwork-api/storage/app/public/uploads/240928/jZtoN0Ak8P1A5Eojw9KndxoV7OkpPJv1J3NVtsBS.docx'  # 替换为您的文档路径
# docx_path = '/Volumes/data/erui/ezwork-api/storage/app/public//translate/jZtoN0Ak8P1A5Eojw9KndxoV7OkpPJv1J3NVtsBS/comments-英语.docx'  # 替换为您的文档路径
comment_id = '3'  # 替换为您要修改的批注 ID
new_text = 'test test'  # 替换为新的批注文本

# document = Document("/Volumes/data/erui/ezwork-api/storage/app/public/uploads/240928/jZtoN0Ak8P1A5Eojw9KndxoV7OkpPJv1J3NVtsBS.docx")
# document.save(docx_path)
# 读取批注
comments = read_comments_from_docx(docx_path)
print("读取的批注:")
for comment in comments:
    print(comment)

# 修改批注
# modify_comment_in_docx(docx_path, comment_id, new_text)