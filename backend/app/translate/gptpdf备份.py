import os
import re
from typing import List, Tuple, Optional, Dict
import logging
import threading
# from . import to_translate
import datetime
from . import common, to_translate
import time
import fitz  # PyMuPDF
import shapely.geometry as sg
from shapely.geometry.base import BaseGeometry
from shapely.validation import explain_validity
import markdown
import pdfkit
import codecs
# from weasyprint import HTML
from pymdownx import superfences
from bs4 import BeautifulSoup
from PIL import Image

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# This Default Prompt Using Chinese and could be changed to other languages.

DEFAULT_PROMPT = """使用markdown语法，将图片中识别到的文字转换为markdown格式输出。你必须做到：
1. 输出和使用识别到的图片的相同的语言，例如，识别到英语的字段，输出的内容必须是英语。
2. 不要解释和输出无关的文字，直接输出图片中的内容。例如，严禁输出 “以下是我根据图片内容生成的markdown文本：”这样的例子，而是应该直接输出markdown。
3. 内容不要包含在```markdown ```中、段落公式使用 $$ $$ 的形式、行内公式使用 $ $ 的形式、忽略掉长直线、忽略掉页码。
再次强调，不要解释和输出无关的文字，直接输出图片中的内容。
"""
DEFAULT_RECT_PROMPT = """图片中用红色框和名称(%s)标注出了一些区域。如果区域是表格或者图片，使用 ![]() 的形式插入到输出内容中，否则直接输出文字内容。
"""
DEFAULT_ROLE_PROMPT = """你是一个PDF文档解析器，使用markdown和latex语法输出图片的内容。
"""


def _is_near(rect1: BaseGeometry, rect2: BaseGeometry, distance: float = 20) -> bool:
    """
    Check if two rectangles are near each other if the distance between them is less than the target.
    """
    return rect1.buffer(0.1).distance(rect2.buffer(0.1)) < distance


def _is_horizontal_near(rect1: BaseGeometry, rect2: BaseGeometry, distance: float = 100) -> bool:
    """
    Check if two rectangles are near horizontally if one of them is a horizontal line.
    """
    result = False
    if abs(rect1.bounds[3] - rect1.bounds[1]) < 0.1 or abs(rect2.bounds[3] - rect2.bounds[1]) < 0.1:
        if abs(rect1.bounds[0] - rect2.bounds[0]) < 0.1 and abs(rect1.bounds[2] - rect2.bounds[2]) < 0.1:
            result = abs(rect1.bounds[3] - rect2.bounds[3]) < distance
    return result


def _union_rects(rect1: BaseGeometry, rect2: BaseGeometry) -> BaseGeometry:
    """
    Union two rectangles.
    """
    return sg.box(*(rect1.union(rect2).bounds))


def _merge_rects(rect_list: List[BaseGeometry], distance: float = 20, horizontal_distance: Optional[float] = None) -> \
        List[BaseGeometry]:
    """
    Merge rectangles in the list if the distance between them is less than the target.
    """
    merged = True
    while merged:
        merged = False
        new_rect_list = []
        while rect_list:
            rect = rect_list.pop(0)
            for other_rect in rect_list:
                if _is_near(rect, other_rect, distance) or (
                        horizontal_distance and _is_horizontal_near(rect, other_rect, horizontal_distance)):
                    rect = _union_rects(rect, other_rect)
                    rect_list.remove(other_rect)
                    merged = True
            new_rect_list.append(rect)
        rect_list = new_rect_list
    return rect_list


def _adsorb_rects_to_rects(source_rects: List[BaseGeometry], target_rects: List[BaseGeometry], distance: float = 10) -> \
        Tuple[List[BaseGeometry], List[BaseGeometry]]:
    """
    Adsorb a set of rectangles to another set of rectangles.
    """
    new_source_rects = []
    for text_area_rect in source_rects:
        adsorbed = False
        for index, rect in enumerate(target_rects):
            if _is_near(text_area_rect, rect, distance):
                rect = _union_rects(text_area_rect, rect)
                target_rects[index] = rect
                adsorbed = True
                break
        if not adsorbed:
            new_source_rects.append(text_area_rect)
    return new_source_rects, target_rects


def _parse_rects(page: fitz.Page) -> List[Tuple[float, float, float, float]]:
    """
    Parse drawings in the page and merge adjacent rectangles.
    """

    # 提取画的内容
    drawings = page.get_drawings()

    # 忽略掉长度小于30的水平直线
    is_short_line = lambda x: abs(x['rect'][3] - x['rect'][1]) < 1 and abs(x['rect'][2] - x['rect'][0]) < 30
    drawings = [drawing for drawing in drawings if not is_short_line(drawing)]

    # 转换为shapely的矩形
    rect_list = [sg.box(*drawing['rect']) for drawing in drawings]

    # 提取图片区域
    images = page.get_image_info()
    image_rects = [sg.box(*image['bbox']) for image in images]

    # 合并drawings和images
    rect_list += image_rects

    merged_rects = _merge_rects(rect_list, distance=10, horizontal_distance=100)
    merged_rects = [rect for rect in merged_rects if explain_validity(rect) == 'Valid Geometry']

    # 将大文本区域和小文本区域分开处理: 大文本相小合并，小文本靠近合并
    is_large_content = lambda x: (len(x[4]) / max(1, len(x[4].split('\n')))) > 5
    small_text_area_rects = [sg.box(*x[:4]) for x in page.get_text('blocks') if not is_large_content(x)]
    large_text_area_rects = [sg.box(*x[:4]) for x in page.get_text('blocks') if is_large_content(x)]
    _, merged_rects = _adsorb_rects_to_rects(large_text_area_rects, merged_rects, distance=0.1) # 完全相交
    _, merged_rects = _adsorb_rects_to_rects(small_text_area_rects, merged_rects, distance=5) # 靠近

    # 再次自身合并
    merged_rects = _merge_rects(merged_rects, distance=10)

    # 过滤比较小的矩形
    merged_rects = [rect for rect in merged_rects if rect.bounds[2] - rect.bounds[0] > 20 and rect.bounds[3] - rect.bounds[1] > 20]

    return [rect.bounds for rect in merged_rects]


def _parse_pdf_to_images(pdf_path: str, output_dir: str = './') -> List[Tuple[str, List[str]]]:
    """
    Parse PDF to images and save to output_dir.
    """
    # 打开PDF文件
    pdf_document = fitz.open(pdf_path)
    image_infos = []

    for page_index, page in enumerate(pdf_document):
        logging.info(f'parse page: {page_index}')
        rect_images = []
        rects = _parse_rects(page)
        for index, rect in enumerate(rects):
            fitz_rect = fitz.Rect(rect)
            # 保存页面为图片
            pix = page.get_pixmap(clip=fitz_rect, matrix=fitz.Matrix(4, 4))
            name = f'{page_index}_{index}.png'
            pix.save(os.path.join(output_dir, name))
            rect_images.append(name)
            # # 在页面上绘制红色矩形
            big_fitz_rect = fitz.Rect(fitz_rect.x0 - 1, fitz_rect.y0 - 1, fitz_rect.x1 + 1, fitz_rect.y1 + 1)
            # 空心矩形
            page.draw_rect(big_fitz_rect, color=(1, 0, 0), width=1)
            # 画矩形区域(实心)
            # page.draw_rect(big_fitz_rect, color=(1, 0, 0), fill=(1, 0, 0))
            # 在矩形内的左上角写上矩形的索引name，添加一些偏移量
            text_x = fitz_rect.x0 + 2
            text_y = fitz_rect.y0 + 10
            text_rect = fitz.Rect(text_x, text_y - 9, text_x + 80, text_y + 2)
            # 绘制白色背景矩形
            page.draw_rect(text_rect, color=(1, 1, 1), fill=(1, 1, 1))
            # 插入带有白色背景的文字
            page.insert_text((text_x, text_y), name, fontsize=10, color=(1, 0, 0))
        page_image_with_rects = page.get_pixmap(matrix=fitz.Matrix(3, 3))
        page_image = os.path.join(output_dir, f'{page_index}.png')
        page_compress_image = os.path.join(output_dir, f'{page_index}-compress.png')
        page_image_with_rects.save(page_image)
        compress_image(page_image,page_compress_image)
        # image_infos.append((page_image, rect_images))
        image_infos.append({'text': page_image,'type':'pdf_img', 'complete': False, 'content': ''})

    pdf_document.close()
    return image_infos


def _gpt_parse_images(
        image_infos: List[Tuple[str, List[str]]],
        prompt_dict: Optional[Dict] = None,
        **args
) -> str:
    """
    Parse images to markdown content.
    """
    if isinstance(prompt_dict, dict) and 'prompt' in prompt_dict:
        prompt = prompt_dict['prompt']
        logging.info("prompt is provided, using user prompt.")
    else:
        prompt = DEFAULT_PROMPT
        logging.info("prompt is not provided, using default prompt.")
    if isinstance(prompt_dict, dict) and 'rect_prompt' in prompt_dict:
        rect_prompt = prompt_dict['rect_prompt']
        logging.info("rect_prompt is provided, using user prompt.")
    else:
        rect_prompt = DEFAULT_RECT_PROMPT
        logging.info("rect_prompt is not provided, using default prompt.")
    if isinstance(prompt_dict, dict) and 'role_prompt' in prompt_dict:
        role_prompt = prompt_dict['role_prompt']
        logging.info("role_prompt is provided, using user prompt.")
    else:
        role_prompt = DEFAULT_ROLE_PROMPT
        logging.info("role_prompt is not provided, using default prompt.")

    for image_index,image_info in enumerate(image_infos):
        user_prompt = prompt
        # if rect_images:
        #     user_prompt += rect_prompt + ', '.join(rect_images)
        image_infos[image_index]['user_prompt']=user_prompt



    # output_path = os.path.join(output_dir, 'output.md')
    # with open(output_path, 'w', encoding='utf-8') as f:
    #     f.write('\n\n'.join(contents))

    # return '\n\n'.join(contents)

def start(trans):
    # 从 trans 中获取文件路径和输出目录
    pdf_path = trans['file_path']
    output_dir = trans['target_path_dir']

    # 允许的最大线程
    threads = trans.get('threads', 10)
    max_threads = max(1, int(threads))

    # 当前执行的索引位置
    run_index = 0
    start_time = datetime.datetime.now()

    # 解析 PDF 文件
    image_infos = _parse_pdf_to_images(pdf_path, output_dir=output_dir)

    _gpt_parse_images(
        image_infos=image_infos,
        prompt_dict=None,
    )

    trans['role_prompt']=DEFAULT_ROLE_PROMPT

    # 使用 threading 方式处理
    max_run = min(max_threads, len(image_infos))
    before_active_count = threading.activeCount()
    event = threading.Event()

    while run_index <= len(image_infos) - 1:
        if threading.activeCount() < max_run + before_active_count:
            if not event.is_set():
                thread = threading.Thread(target=to_translate.get, args=(trans, event, image_infos, run_index))
                thread.start()
                run_index += 1
            else:
                return False

    while True:
        complete = True
        for image_info in image_infos:
            if not image_info['complete']:
                complete = False
        if complete:
            break
        else:
            time.sleep(1)

    # print(image_infos)
    # 处理完成后，写入结果
    try:
        # c = canvas.Canvas(trans['target_file'], pagesize=letter)
        # text = c.beginText(40, 750)  # 设置文本开始的位置
        # text.setFont("Helvetica", 12)  # 设置字体和大小
        md_file = os.path.join(output_dir, 'output.md')
        with open(md_file, 'w', encoding='utf-8') as file:
            for image_info in image_infos:
            # text.textLine(image_info['text'])  # 添加文本行
            # text.textLine("")  # 添加空行作为分隔
            # write_pdf(c, image_info['text']);
                file.write(image_info['text'] + '\n')
        # write_to_pdf(md_file, trans['target_file'])
        html_to_pdf(output_dir, md_file, trans['target_file'])
        # c.save()  # 保存 PDF 文件
    except Exception as e:
        print(f"生成pdf失败： {md_file}: {e}")
        return False

    end_time = datetime.datetime.now()
    spend_time = common.display_spend(start_time, end_time)
    # translate.complete(trans, len(image_infos), spend_time)
    return True

def compress_image(image_file,compress_image_file):
    img=Image.open(image_file)
    img_resized=img.resize((img.width//2, img.height//2), resample=Image.Resampling.NEAREST)
    img_resized.save(compress_image_file,quality=30)


def html_to_pdf(output_dir, md_file, pdf_file):
    extensions = [
        'toc',  # 目录，[toc]
        'extra',  # 缩写词、属性列表、释义列表、围栏式代码块、脚注、在HTML的Markdown、表格
    ]
    third_party_extensions = [
        'mdx_math',  # KaTeX数学公式，$E=mc^2$和$$E=mc^2$$
        'markdown_checklist.extension',  # checklist，- [ ]和- [x]
        'pymdownx.magiclink',  # 自动转超链接，
        'pymdownx.caret',  # 上标下标，
        'pymdownx.superfences',  # 多种块功能允许嵌套，各种图表
        'pymdownx.betterem',  # 改善强调的处理(粗体和斜体)
        'pymdownx.mark',  # 亮色突出文本
        'pymdownx.highlight',  # 高亮显示代码
        'pymdownx.tasklist',  # 任务列表
        'pymdownx.tilde',  # 删除线
    ]
    extensions.extend(third_party_extensions)
    extension_configs = {
        'mdx_math': {
            'enable_dollar_delimiter': True  # 允许单个$
        },
        'pymdownx.superfences': {
            "custom_fences": [
                {
                    'name': 'mermaid',  # 开启流程图等图
                    'class': 'mermaid',
                    'format': superfences.fence_div_format
                }
            ]
        },
        'pymdownx.highlight': {
            'linenums': True,  # 显示行号
            'linenums_style': 'pymdownx-inline'  # 代码和行号分开
        },
        'pymdownx.tasklist': {
            'clickable_checkbox': True,  # 任务列表可点击
        }
    }
    with codecs.open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()
    
    html_file = os.path.join(output_dir, 'output.html')
    html_final_file = os.path.join(output_dir, 'output-final.html')
    html_content = markdown.markdown(md_content, extensions=extensions, extension_configs=extension_configs)
    with codecs.open(html_file, "w", encoding="utf-8") as f:
        # 加入文件头防止中文乱码
        f.write('<meta content="text/html; charset=utf-8" http-equiv="Content-Type"/>')
        f.write('<script type="text/javascript" src="https://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-MML-AM_SVG"></script>')
        f.write(html_content)

     
    # 优化html中的图片信息
    with codecs.open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, features="lxml")
        image_content = soup.find_all("img")
        for i in image_content:
            i["style"] = "max-width:100%; overflow:hidden;"
        with codecs.open(html_final_file, "w", encoding="utf-8") as g:
            g.write(soup.prettify())
     
    pdfkit.from_file(html_final_file, pdf_file)

