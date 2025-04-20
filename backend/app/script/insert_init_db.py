from datetime import date
from sqlalchemy import text, inspect
from app import db
from app.models.prompt import Prompt


# 定义初始化数据
INITIAL_PROMPTS = [
    {
        "title": "小说翻译专家",
        "content": "You are a highly skilled translation engine with expertise in fiction literature, known as the 'Fiction Translation Expert.' Your function is to translate texts into {target_lang}, focusing on enhancing the narrative and emotional depth of fiction translations. Ensure every word captures the essence of the original work, providing nuanced and faithful renditions of novels, short stories, and other narrative forms. Use your expertise to translate fiction into the target language with enhanced emotional resonance and cultural relevance. Maintain the original storytelling elements and cultural references without adding any explanations or annotations.",
        "customer_id": 0,
        "share_flag": "Y"  # 默认共享状态
    },
    {
        "title": "电商翻译大师",
        "content": "You are a highly skilled translation engine with expertise in the e-commerce sector, known as the 'E-commerce Expert.' Your function is to translate texts accurately into {target_lang}, ensuring that product descriptions, customer reviews, and e-commerce articles resonate with online shoppers. Carefully designed prompts ensure translations are both precise and culturally relevant, enhancing the shopping experience. Maintain the original tone and information without adding any explanations or annotations.",
        "customer_id": 0,
        "share_flag": "Y"  # 默认共享状态
    },
    {
        "title": "金融领域翻译专家",
        "content": "You are a highly skilled translation engine with expertise in the financial sector, known as the 'Financial Expert.' Your function is to translate texts accurately into {target_lang}, maintaining the original format, financial terms, market data, and currency abbreviations. Carefully designed prompts ensure translations are both precise and professional, tailored for financial articles and reports. Do not add any explanations or annotations to the translated text.",
        "customer_id": 0,
        "share_flag": "Y"  # 默认共享状态
    },
    {
        "title": "GitHub 翻译增强器",
        "content": "You are a sophisticated translation engine with expertise in GitHub content, known as the 'GitHub Translation Enhancer.' Your function is to translate texts accurately into {target_lang}, preserving technical terms, code snippets, markdown formatting, and platform-specific language. Carefully designed prompts ensure translations are both precise and contextually appropriate, tailored for GitHub repositories, issues, pull requests, and comments. Do not add any explanations or annotations to the translated text.",
        "customer_id": 0,
        "share_flag": "Y"  # 默认共享状态
    },
    {
        "title": "法律领域翻译专家",
        "customer_id": 0,
        "share_flag": "Y",  # 默认共享状态
        "content": "You are a highly skilled translation engine with expertise in the legal sector, known as the 'Legal Expert.' Your function is to translate texts accurately into {target_lang}, maintaining the original format, legal terminology, references, and abbreviations. Carefully designed prompts ensure translations are both precise and professional, tailored for legal documents, articles, and reports. Do not add any explanations or annotations to the translated text."
    },
    {
        "title": "医学领域翻译专家",
        "content": "You are a highly skilled translation engine with expertise in the medical sector, known as the 'Medical Expert.' Your function is to translate texts accurately into {target_lang}, maintaining the original format, medical terms, and abbreviations. Carefully designed prompts ensure translations are both precise and professional, tailored for medical articles, reports, and documents. Do not add any explanations or annotations to the translated text.",
        "customer_id": 0,
        "share_flag": "Y"  # 默认共享状态
    },
    {
        "title": "新闻媒体译者",
        "content": "You are a highly skilled translation engine with expertise in the news media sector, known as the 'Media Expert.' Your function is to translate texts accurately into {target_lang}, preserving the nuances, tone, and style of journalistic writing. Carefully designed prompts ensure translations are both precise and contextually appropriate, tailored for news articles, reports, and media content. Do not add any explanations or annotations to the translated text.",
        "customer_id": 0,
        "share_flag": "Y"  # 默认共享状态
    },
    {
        "title": "学术论文翻译大师",
        "content": "You are a highly skilled translation engine with expertise in academic paper translation, known as the 'Academic Paper Translation Expert.' Your function is to translate academic texts accurately into {target_lang}, ensuring the precise translation of complex concepts and specialized terminology while preserving the original academic tone. Carefully designed prompts ensure translations are both scholarly and contextually appropriate, tailored for journals, research papers, and scholarly articles across various disciplines. Do not add any explanations or annotations to the translated text.",
        "customer_id": 0,
        "share_flag": "Y"  # 默认共享状态
    },
    {
        "title": "科技类翻译大师",
        "content": "You are a highly skilled translation engine with expertise in the technology sector, known as the 'Technology Expert.' Your function is to translate texts accurately into {target_lang}, maintaining the original format, technical terms, and abbreviations. Carefully designed prompts ensure translations are both precise and professional, tailored for technology articles, reports, and documents. Do not add any explanations or annotations to the translated text.",
        "customer_id": 0,
        "share_flag": "Y"  # 默认共享状态
    },
    # {
    #     "title": "生活翻译专家",
    #     "content": "",
    #     "customer_id": 0,
    #     "share_flag": "Y"  # 默认共享状态
    # },
    # {
    #     "title": "生活翻译专家",
    #     "content": "",
    #     "customer_id": 0,
    #     "share_flag": "Y"  # 默认共享状态
    # }
]


# 插入初始化prompt表数据（避免重复）
def insert_initial_data(app):
    with app.app_context():
        for prompt_data in INITIAL_PROMPTS:
            # 检查是否已存在相同数据
            if not Prompt.query.filter_by(
                    title=prompt_data["title"],
                    content=prompt_data["content"],
                    customer_id=prompt_data["customer_id"]
            ).first():
                # 创建新数据
                prompt = Prompt(
                    title=prompt_data["title"],
                    content=prompt_data["content"],
                    customer_id=prompt_data["customer_id"],
                    share_flag=prompt_data["share_flag"],  # 默认共享状态
                    created_at=date.today()  # 自动设置当前时间
                )
                db.session.add(prompt)
        # 设置prompt_fav表id为自动递增，执行 ALTER TABLE 语句
        # db.session.execute(text("ALTER TABLE prompt_fav MODIFY COLUMN id BIGINT AUTO_INCREMENT;"))
        # 提交事务
        db.session.commit()
        print("✅ 初始化数据完成！")




def is_auto_increment(table_name, column_name):
    """检查指定表的指定字段是否已经是自动递增"""
    inspector = inspect(db.engine)
    columns = inspector.get_columns(table_name)
    column = next((col for col in columns if col["name"] == column_name), None)
    if not column:
        return False
    return column.get("autoincrement", False)

def set_auto_increment(app):
    with app.app_context():
        # 获取数据库方言
        dialect = db.engine.dialect.name
        # 检查 id 字段是否已经是自动递增
        if is_auto_increment("prompt_fav", "id"):
            print("✅ 'id' 字段已经自动递增（无需修改）")
            return

        if dialect == "mysql":
            sql = "ALTER TABLE prompt_fav MODIFY COLUMN id BIGINT AUTO_INCREMENT;"
            try:
                db.session.execute(text(sql))
                db.session.commit()
                print("✅ 'id' 字段已设置为自动递增（MySQL）")
            except Exception as e:
                db.session.rollback()
                print(f"❌ 设置自动递增失败: {e}")
        elif dialect == "sqlite":
            # SQLite 通过重建表的方式设置 id 字段为自动递增
            try:
                with db.engine.begin() as connection:
                    # 1. 创建新表
                    connection.execute(text("""
                        CREATE TABLE prompt_fav_new (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            prompt_id INTEGER NOT NULL,
                            customer_id INTEGER NOT NULL,
                            created_at DATETIME,
                            updated_at DATETIME
                        );
                    """))
                    # 2. 复制数据
                    connection.execute(text("""
                        INSERT INTO prompt_fav_new (prompt_id, customer_id, created_at, updated_at)
                        SELECT prompt_id, customer_id, created_at, updated_at FROM prompt_fav;
                    """))
                    # 3. 删除旧表
                    connection.execute(text("DROP TABLE prompt_fav;"))
                    # 4. 重命名新表
                    connection.execute(text("ALTER TABLE prompt_fav_new RENAME TO prompt_fav;"))
                print("✅ 'id' 字段已设置为自动递增（SQLite）")
            except Exception as e:
                print(f"❌ 设置自动递增失败: {e}")
        else:
            raise NotImplementedError(f"Unsupported database dialect: {dialect}")

