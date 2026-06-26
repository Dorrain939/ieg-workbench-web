#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清理 index.html 中 <style> 块内的重复 CSS 规则，只保留最后一份。"""

import re
import sys

def clean_css(css_text):
    """
    非常简单的 CSS 重复规则清理：
    - 按 } 分割规则块
    - 用选择器作为 key，保留最后出现的规则
    - 保留注释和 @media 等 at-rule（不处理，直接保留）
    """
    # 先提取所有 at-rules (@media, @keyframes 等) 和非 at-rules
    # 简单策略：按顶级 { } 分割，保留最后一个同名选择器
    
    # 用正则找到所有顶级规则块（不匹配嵌套在 {} 内的）
    # 简单做法：按行处理，记录每个规则的选择器
    
    lines = css_text.split('\n')
    rules = []  # list of (selector_text, start_line_idx, end_line_idx)
    i = 0
    in_at_rule = False
    at_rule_depth = 0
    
    # 更简单粗暴的方法：
    # 直接在整个 CSS 文本中，把重复的完整规则块删掉
    # 识别方式：如果同一个选择器出现多次，只保留最后一次
    
    # 用正则找到所有选择器 + 规则体的组合
    # pattern: 选择器 { ... }
    # 但 CSS 注释和字符串中的 {} 会干扰
    
    # 最务实的方法：按 <style> 标签读取后，
    # 把文件从中间切开，保留前半部分（原始 CSS）和后半部分（重复的 CSS），只留一份
    # 但这样不准确
    
    # 实际最简单的方案：
    # 直接手动指定要删除的重复块范围
    # 根据 grep 结果，重复规则大概从某个位置开始
    # 但不通用
    
    # 改用这个方法：
    # 1. 把 CSS 按 } 分割成规则块
    # 2. 每个规则块取第一行的选择器作为 key
    # 3. 如果 key 已出现过，删掉之前的
    # 缺点：会误删 @media 内的规则；但当前文件没有复杂嵌套
    
    blocks = []
    current_block = ''
    depth = 0
    in_comment = False
    
    for line in lines:
        stripped = line.strip()
        
        # 非常简单的注释处理
        if '/*' in stripped:
            in_comment = True
        if '*/' in stripped:
            in_comment = False
            continue
        if in_comment:
            continue
            
        current_block += line + '\n'
        
        # 计算 {} 深度
        depth += stripped.count('{') - stripped.count('}')
        
        if depth == 0 and current_block.strip():
            blocks.append(current_block)
            current_block = ''
    
    # 现在 blocks 里是每个 CSS 规则块
    # 提取每个块的选择器（第一行的选择器部分）
    def get_selector(block_text):
        first_line = block_text.strip().split('\n')[0].strip()
        # 去掉 { 后面的内容
        if '{' in first_line:
            return first_line[:first_line.index('{')].strip()
        return first_line
    
    # 保留最后一个同名选择器
    seen = {}
    for i, block in enumerate(blocks):
        sel = get_selector(block)
        if sel:
            seen[sel] = i
    
    # 重建 CSS
    # 保留 at-rules（@media 等）和注释
    # 简单做法：如果选择器重复，删掉前面的
    
    # 更简单的做法：直接把 blocks 中重复选择器的最早出现删掉
    to_remove = set()
    selector_positions = {}
    for i, block in enumerate(blocks):
        sel = get_selector(block)
        if not sel:
            continue
        if sel in selector_positions:
            to_remove.add(selector_positions[sel])
        selector_positions[sel] = i
    
    cleaned_blocks = [b for i, b in enumerate(blocks) if i not in to_remove]
    
    return '\n'.join(cleaned_blocks)

def main():
    filepath = '/Users/dorrain/Desktop/poster-web/static/index.html'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到 <style> 和 </style> 之间的内容
    style_start = content.index('<style>')
    style_end = content.index('</style>')
    
    css_before = content[:style_start + len('<style>')]
    css_content = content[style_start + len('<style>'):style_end]
    css_after = content[style_end:]
    
    print(f'CSS 长度（清理前）: {len(css_content)} 字符')
    
    cleaned = clean_css(css_content)
    
    print(f'CSS 长度（清理后）: {len(cleaned)} 字符')
    
    new_content = css_before + cleaned + css_after
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print('✓ 已清理重复 CSS 规则并写回文件')

if __name__ == '__main__':
    main()
