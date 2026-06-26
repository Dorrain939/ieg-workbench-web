"""skills 子包：内置 AI 工作场景。

每个 skill 模块导出 run(project, params, kb, llm, context=None) -> Iterator[dict]
事件类型：token / artifact / progress / ask / error / done
"""
