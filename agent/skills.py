import os
import frontmatter

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "..", "skills")

def load_all_skills(skills_dir: str = SKILLS_DIR) -> dict[str, dict]:
    """进程启动时调用一次，扫描并解析所有 SKILL.md 元数据"""
    skills = {}
    for skill_name in os.listdir(skills_dir):
        skill_md_path = os.path.join(skills_dir, skill_name, "SKILL.md")
        if not os.path.isfile(skill_md_path):
            continue
        post = frontmatter.load(skill_md_path)
        skills[post.metadata["name"]] = {
            **post.metadata,
            "content": post.content,
            "dir": os.path.join(skills_dir, skill_name),
        }
    return skills

def filter_skills_by_agent(skills: dict, agent_name: str) -> dict:
    return {k: v for k, v in skills.items() if v.get("agent") == agent_name}

def build_skill_prompt(skills: dict) -> str:
    if not skills:
        return ""
    lines = ["\n\n## 可用技能列表（如与当前用户请求相关，调用 load_skill 工具加载完整操作指南）:"]
    for name, meta in skills.items():
        lines.append(f"- {name}: {meta['description']}")
    return "\n".join(lines)

# 加载skill
ALL_SKILLS = load_all_skills()
