

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;



-- --------------------------------------------------------

--
-- 表的结构 `alembic_version`
--

CREATE TABLE `alembic_version` (
  `version_num` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- 表的结构 `comparison`
--

CREATE TABLE `comparison` (
  `id` int(11) NOT NULL,
  `title` text NOT NULL,
  `origin_lang` text NOT NULL,
  `target_lang` text NOT NULL,
  `share_flag` text,
  `added_count` int(11) DEFAULT NULL,
  `content` longtext NOT NULL,
  `customer_id` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `deleted_flag` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- 表的结构 `comparison_fav`
--

CREATE TABLE `comparison_fav` (
  `id` int(11) NOT NULL,
  `comparison_id` int(11) NOT NULL,
  `customer_id` int(11) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- 表的结构 `customer`
--

CREATE TABLE `customer` (
  `id` int(11) NOT NULL,
  `customer_no` text,
  `phone` text,
  `name` text,
  `password` text NOT NULL,
  `email` text NOT NULL,
  `level` text,
  `status` text,
  `deleted_flag` text,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `storage` bigint(20) DEFAULT NULL,
  `total_storage` bigint(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- 转存表中的数据 `customer`
--

INSERT INTO `customer` (`id`, `customer_no`, `phone`, `name`, `password`, `email`, `level`, `status`, `deleted_flag`, `created_at`, `updated_at`, `storage`, `total_storage`) VALUES
(1, NULL, NULL, NULL, 'scrypt:32768:8:1$FTZLV5ptzN1KMmIS$aa80b88763b514b30f647130cd535b39cdbab617cebebedab8b954e2616f72ca01f180520a82a61dbf63ea6e88618aa039287ed540857e110ffabd0252c3ac3f', 'test', 'common', 'enabled', 'N', '2025-04-20 08:17:17', '2025-04-22 02:48:49', 7354362, 104857600);

-- --------------------------------------------------------

--
-- 表的结构 `prompt`
--

CREATE TABLE `prompt` (
  `id` int(11) NOT NULL,
  `title` text NOT NULL,
  `share_flag` text,
  `added_count` int(11) DEFAULT NULL,
  `content` longtext NOT NULL,
  `customer_id` int(11) DEFAULT NULL,
  `created_at` date DEFAULT NULL,
  `updated_at` date DEFAULT NULL,
  `deleted_flag` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- 转存表中的数据 `prompt`
--

INSERT INTO `prompt` (`id`, `title`, `share_flag`, `added_count`, `content`, `customer_id`, `created_at`, `updated_at`, `deleted_flag`) VALUES
(1, '小说翻译专家', 'Y', 0, 'You are a highly skilled translation engine with expertise in fiction literature, known as the \'Fiction Translation Expert.\' Your function is to translate texts into {target_lang}, focusing on enhancing the narrative and emotional depth of fiction translations. Ensure every word captures the essence of the original work, providing nuanced and faithful renditions of novels, short stories, and other narrative forms. Use your expertise to translate fiction into the target language with enhanced emotional resonance and cultural relevance. Maintain the original storytelling elements and cultural references without adding any explanations or annotations.', 0, '2025-04-20', NULL, 'N'),
(2, '电商翻译大师', 'Y', 0, 'You are a highly skilled translation engine with expertise in the e-commerce sector, known as the \'E-commerce Expert.\' Your function is to translate texts accurately into {target_lang}, ensuring that product descriptions, customer reviews, and e-commerce articles resonate with online shoppers. Carefully designed prompts ensure translations are both precise and culturally relevant, enhancing the shopping experience. Maintain the original tone and information without adding any explanations or annotations.', 0, '2025-04-20', NULL, 'N'),
(3, '金融领域翻译专家', 'Y', 0, 'You are a highly skilled translation engine with expertise in the financial sector, known as the \'Financial Expert.\' Your function is to translate texts accurately into {target_lang}, maintaining the original format, financial terms, market data, and currency abbreviations. Carefully designed prompts ensure translations are both precise and professional, tailored for financial articles and reports. Do not add any explanations or annotations to the translated text.', 0, '2025-04-20', NULL, 'N'),
(4, 'GitHub 翻译增强器', 'Y', 0, 'You are a sophisticated translation engine with expertise in GitHub content, known as the \'GitHub Translation Enhancer.\' Your function is to translate texts accurately into {target_lang}, preserving technical terms, code snippets, markdown formatting, and platform-specific language. Carefully designed prompts ensure translations are both precise and contextually appropriate, tailored for GitHub repositories, issues, pull requests, and comments. Do not add any explanations or annotations to the translated text.', 0, '2025-04-20', NULL, 'N'),
(5, '法律领域翻译专家', 'Y', 0, 'You are a highly skilled translation engine with expertise in the legal sector, known as the \'Legal Expert.\' Your function is to translate texts accurately into {target_lang}, maintaining the original format, legal terminology, references, and abbreviations. Carefully designed prompts ensure translations are both precise and professional, tailored for legal documents, articles, and reports. Do not add any explanations or annotations to the translated text.', 0, '2025-04-20', NULL, 'N'),
(6, '医学领域翻译专家', 'Y', 0, 'You are a highly skilled translation engine with expertise in the medical sector, known as the \'Medical Expert.\' Your function is to translate texts accurately into {target_lang}, maintaining the original format, medical terms, and abbreviations. Carefully designed prompts ensure translations are both precise and professional, tailored for medical articles, reports, and documents. Do not add any explanations or annotations to the translated text.', 0, '2025-04-20', NULL, 'N'),
(7, '新闻媒体译者', 'Y', 0, 'You are a highly skilled translation engine with expertise in the news media sector, known as the \'Media Expert.\' Your function is to translate texts accurately into {target_lang}, preserving the nuances, tone, and style of journalistic writing. Carefully designed prompts ensure translations are both precise and contextually appropriate, tailored for news articles, reports, and media content. Do not add any explanations or annotations to the translated text.', 0, '2025-04-20', NULL, 'N'),
(8, '学术论文翻译大师', 'Y', 0, 'You are a highly skilled translation engine with expertise in academic paper translation, known as the \'Academic Paper Translation Expert.\' Your function is to translate academic texts accurately into {target_lang}, ensuring the precise translation of complex concepts and specialized terminology while preserving the original academic tone. Carefully designed prompts ensure translations are both scholarly and contextually appropriate, tailored for journals, research papers, and scholarly articles across various disciplines. Do not add any explanations or annotations to the translated text.', 0, '2025-04-20', NULL, 'N'),
(9, '科技类翻译大师', 'Y', 0, 'You are a highly skilled translation engine with expertise in the technology sector, known as the \'Technology Expert.\' Your function is to translate texts accurately into {target_lang}, maintaining the original format, technical terms, and abbreviations. Carefully designed prompts ensure translations are both precise and professional, tailored for technology articles, reports, and documents. Do not add any explanations or annotations to the translated text.', 0, '2025-04-20', NULL, 'N');

-- --------------------------------------------------------

--
-- 表的结构 `prompt_fav`
--

CREATE TABLE `prompt_fav` (
  `id` int(11) NOT NULL,
  `prompt_id` int(11) NOT NULL,
  `customer_id` int(11) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- 表的结构 `send_code`
--

CREATE TABLE `send_code` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `send_type` int(11) NOT NULL,
  `send_to` text NOT NULL,
  `code` text NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- 表的结构 `setting`
--

CREATE TABLE `setting` (
  `id` int(11) NOT NULL,
  `alias` text,
  `value` longtext,
  `serialized` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `deleted_flag` text,
  `group` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- 表的结构 `translate`
--

CREATE TABLE `translate` (
  `id` int(11) NOT NULL,
  `translate_no` text,
  `uuid` text,
  `customer_id` int(11) DEFAULT NULL,
  `rand_user_id` text,
  `origin_filename` text NOT NULL,
  `origin_filepath` text NOT NULL,
  `target_filepath` text NOT NULL,
  `status` text,
  `start_at` datetime DEFAULT NULL,
  `end_at` datetime DEFAULT NULL,
  `deleted_flag` text,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `origin_filesize` bigint(20) DEFAULT NULL,
  `target_filesize` bigint(20) DEFAULT NULL,
  `lang` text,
  `model` text,
  `prompt` text,
  `api_url` text,
  `api_key` text,
  `threads` int(11) DEFAULT NULL,
  `failed_reason` longtext,
  `failed_count` int(11) DEFAULT NULL,
  `word_count` int(11) DEFAULT NULL,
  `backup_model` text,
  `md5` text,
  `type` text,
  `origin_lang` text,
  `process` float DEFAULT NULL,
  `doc2x_flag` text,
  `doc2x_secret_key` text,
  `prompt_id` bigint(20) DEFAULT NULL,
  `comparison_id` bigint(20) DEFAULT NULL,
  `size` bigint(20) DEFAULT NULL,
  `server` text,
  `app_id` text,
  `app_key` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- 转存表中的数据 `translate`
--

INSERT INTO `translate` (`id`, `translate_no`, `uuid`, `customer_id`, `rand_user_id`, `origin_filename`, `origin_filepath`, `target_filepath`, `status`, `start_at`, `end_at`, `deleted_flag`, `created_at`, `updated_at`, `origin_filesize`, `target_filesize`, `lang`, `model`, `prompt`, `api_url`, `api_key`, `threads`, `failed_reason`, `failed_count`, `word_count`, `backup_model`, `md5`, `type`, `origin_lang`, `process`, `doc2x_flag`, `doc2x_secret_key`, `prompt_id`, `comparison_id`, `size`, `server`, `app_id`, `app_key`) VALUES
(1, 'TRANS20250422104842', '45680b74-b63b-431a-82a2-5356353a9f64', 1, NULL, '“泉涌情深：润兵甘泉的故事”.docx', 'F:\\doctranslator\\storage\\uploads\\2025-04-22\\“泉涌情深：润兵甘泉的故事”.docx', 'F:\\doctranslator\\storage\\translate\\2025-04-22\\“泉涌情深：润兵甘泉的故事”.docx', 'done', '2025-04-22 10:48:50', '2025-04-22 10:49:50', 'N', '2025-04-22 02:48:43', '2025-04-22 02:49:50', 2451642, 0, '英语', 'THUDM/GLM-4-32B-0414', '你是一个文档翻译助手，请将以下文本、单词或短语直接翻译成{target_lang}，不返回原文本。如果文本中包含{target_lang}文本、特殊名词（比如邮箱、品牌名、单位名词如mm、px、℃等）、无法翻译等特殊情况，请直接返回原文而无需解释原因。遇到无法翻译的文本直接返回原内容。保留多余空格。', 'https://api.siliconflow.cn', 'sk-nwidhtjmodqbljlmpjuvudhdhidhjnntjfcpskrvixvwogbl', 5, NULL, 0, 0, 'deepseek-chat', 'e0fc86bdc48cd7dda19a7b193e7c36ca', 'trans_text_only_new', '', 100, 'N', '', 0, NULL, 2451360, 'openai', '', '');

-- --------------------------------------------------------

--
-- 表的结构 `user`
--

CREATE TABLE `user` (
  `id` int(11) NOT NULL,
  `name` text,
  `password` text NOT NULL,
  `email` text NOT NULL,
  `deleted_flag` text,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- 转存表中的数据 `user`
--

INSERT INTO `user` (`id`, `name`, `password`, `email`, `deleted_flag`, `created_at`, `updated_at`) VALUES
(1, 'admin', '123456', 'admin', 'N', NULL, NULL);

--
-- 转储表的索引
--

--
-- 表的索引 `alembic_version`
--
ALTER TABLE `alembic_version`
  ADD PRIMARY KEY (`version_num`(255));

--
-- 表的索引 `comparison`
--
ALTER TABLE `comparison`
  ADD PRIMARY KEY (`id`);

--
-- 表的索引 `comparison_fav`
--
ALTER TABLE `comparison_fav`
  ADD PRIMARY KEY (`id`);

--
-- 表的索引 `customer`
--
ALTER TABLE `customer`
  ADD PRIMARY KEY (`id`);

--
-- 表的索引 `prompt`
--
ALTER TABLE `prompt`
  ADD PRIMARY KEY (`id`);

--
-- 表的索引 `prompt_fav`
--
ALTER TABLE `prompt_fav`
  ADD PRIMARY KEY (`id`);

--
-- 表的索引 `send_code`
--
ALTER TABLE `send_code`
  ADD PRIMARY KEY (`id`);

--
-- 表的索引 `setting`
--
ALTER TABLE `setting`
  ADD PRIMARY KEY (`id`);

--
-- 表的索引 `translate`
--
ALTER TABLE `translate`
  ADD PRIMARY KEY (`id`);

--
-- 表的索引 `user`
--
ALTER TABLE `user`
  ADD PRIMARY KEY (`id`);

--
-- 在导出的表使用AUTO_INCREMENT
--

--
-- 使用表AUTO_INCREMENT `comparison`
--
ALTER TABLE `comparison`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- 使用表AUTO_INCREMENT `comparison_fav`
--
ALTER TABLE `comparison_fav`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- 使用表AUTO_INCREMENT `customer`
--
ALTER TABLE `customer`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- 使用表AUTO_INCREMENT `prompt`
--
ALTER TABLE `prompt`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- 使用表AUTO_INCREMENT `prompt_fav`
--
ALTER TABLE `prompt_fav`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- 使用表AUTO_INCREMENT `send_code`
--
ALTER TABLE `send_code`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- 使用表AUTO_INCREMENT `setting`
--
ALTER TABLE `setting`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- 使用表AUTO_INCREMENT `translate`
--
ALTER TABLE `translate`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- 使用表AUTO_INCREMENT `user`
--
ALTER TABLE `user`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
