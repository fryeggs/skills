---
name: cli-anything
description: "Generate CLI interfaces for desktop software and applications."
---

# CLI-Anything Skill

Generate agent-native CLI for any desktop software (GIMP, Blender, Audacity, etc.)

## 触发条件（满足任一即可）

- 用户要给桌面软件生成 CLI
- 用户要"命令行控制"某个已安装的软件
- 用户提到：GIMP, Blender, Audacity, FreeCAD, Krita, Draw.io, Zotero, Obsidian, MuseScore
- 用户说：让 XX 软件支持命令行、生成 XX 的 CLI
- 用户说：make XX agent-native
- 用户提供软件安装路径，要生成对应 CLI
- 用户要自动化桌面软件操作

## 快速使用

```bash
# 在 Claude Code 中使用 slash command
/cli-anything <软件路径>

# 示例
/cli-anything ./gimp           # GIMP 图像编辑器
/cli-anything ./blender        # Blender 3D
/cli-anything ./path/to/app    # 任意软件
```

## 支持的软件 (50+)

### 图像/3D
| 软件 | 命令 |
|------|------|
| GIMP | `/cli-anything ./gimp` |
| Blender | `/cli-anything ./blender` |
| FreeCAD | `/cli-anything ./freecad` |
| Krita | `/cli-anything ./krita` |
| Inkscape | `/cli-anything ./inkscape` |

### 音频/视频
| 软件 | 命令 |
|------|------|
| Audacity | `/cli-anything ./audacity` |
| MuseScore | `/cli-anything ./musescore` |
| Kdenlive | `/cli-anything ./kdenlive` |

### 生产力工具
| 软件 | 命令 |
|------|------|
| Draw.io | `/cli-anything ./drawio` |
| Zotero | `/cli-anything ./zotero` |
| Obsidian | `/cli-anything ./obsidian` |

### 开发工具
| 软件 | 命令 |
|------|------|
| ComfyUI | `/cli-anything ./comfyui` |
| Godot | `/cli-anything ./godot` |
| RenderDoc | `/cli-anything ./renderdoc` |

## 示例触发话术

| 用户可能说的话 | 解析 |
|--------------|------|
| "帮我给 GIMP 生成 CLI" | 触发 cli-anything |
| "Blender 能用命令行控制吗" | 触发 cli-anything |
| "让这个软件支持 agent" | 触发 cli-anything |
| "/cli-anything ./path/to/app" | 直接调用 |
| "我要自动化 Zotero 的操作" | 触发 cli-anything |
| "FreeCAD 有命令行接口吗" | 触发 cli-anything |

## 工作流程

1. 分析软件源码/API
2. 设计命令组
3. 生成 Click CLI
4. 编写测试
5. 文档化
6. 发布到 PATH

## CLI-Hub 预置包

```bash
pip install cli-anything-hub
cli-hub install <name>   # 安装预置 CLI
cli-hub search <query>   # 搜索可用 CLI
```

## 何时不用

- 网站/网页 → 用 `opencli`
- GitHub 搜索 → 用 `github-suite`
- 视频转写 → 用 `web-content-learner`
