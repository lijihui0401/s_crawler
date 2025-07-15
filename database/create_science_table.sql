-- 创建Science文章表
CREATE TABLE IF NOT EXISTS `science` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(500) NOT NULL COMMENT '文章标题',
  `authors` text COMMENT '作者列表',
  `journal` varchar(100) DEFAULT 'Science' COMMENT '期刊名称',
  `journal_info` varchar(255) DEFAULT NULL COMMENT '期刊详细信息',
  `abstract` text COMMENT '摘要',
  `doi` varchar(100) DEFAULT NULL COMMENT 'DOI号',
  `url` varchar(500) NOT NULL COMMENT '文章URL',
  `pdf_url` varchar(500) DEFAULT NULL COMMENT 'PDF下载链接',
  `download_path` varchar(500) DEFAULT NULL COMMENT '本地下载路径',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_doi` (`doi`),
  KEY `idx_title` (`title`(255)),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Science期刊文章表';

-- 创建索引优化查询性能
CREATE INDEX idx_science_doi ON science(doi);
CREATE INDEX idx_science_title ON science(title(255));