import re
import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from litemind.registry.service import ToolRegistry


class WorkflowPlanner:
    """
    Goal Analyzer & Dynamic DAG Generator.
    Analyzes user goal, desired output type, uploaded files, and generates a structured dependency task DAG.
    """

    @classmethod
    def analyze_goal_and_plan(
        cls,
        user_request: str,
        output_type: str = "presentation",
        file_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dynamically construct a workflow task DAG based on the goal intent.
        """
        lower_req = user_request.lower()

        # Identify output intention
        if "comic" in lower_req or output_type == "comic":
            target_output = "comic"
        elif "presentation" in lower_req or "slide" in lower_req or "pptx" in lower_req:
            target_output = "presentation"
        elif "pdf" in lower_req or "doc" in lower_req or "report" in lower_req or "paper" in lower_req:
            target_output = "document"
        elif "code" in lower_req or "app" in lower_req or "python" in lower_req or "website" in lower_req or "logo" in lower_req:
            target_output = "code_or_asset"
        else:
            target_output = output_type

        tasks = []

        # Step 1: Research / Fact Analysis
        needs_web_research = any(w in lower_req for w in ["latest", "news", "facts", "research", "find", "search", "india", "space", "energy", "climate"]) or not file_context

        import uuid
        prefix = str(uuid.uuid4())[:8]

        id_doc_extract = f"task_doc_extract_{prefix}"
        id_research = f"task_research_{prefix}"
        id_write_content = f"task_write_content_{prefix}"
        id_generate_images = f"task_generate_images_{prefix}"
        id_compile_pptx = f"task_compile_pptx_{prefix}"
        id_write_report = f"task_write_report_{prefix}"
        id_compile_pdf = f"task_compile_pdf_{prefix}"
        id_write_code = f"task_write_code_{prefix}"
        id_write_comic = f"task_write_comic_{prefix}"
        id_compile_comic = f"task_compile_comic_{prefix}"
        id_quality_review = f"task_quality_review_{prefix}"

        if file_context:
            tasks.append({
                "id": id_doc_extract,
                "task_name": "Extract & Analyze Uploaded Document Context",
                "category": "Research",
                "required_capability": "data_extraction",
                "dependencies": [],
                "input_prompt": f"Extract key sections, facts, and structure from the provided file content regarding: '{user_request}'"
            })
            research_dep = [id_doc_extract]
        elif needs_web_research:
            tasks.append({
                "id": id_research,
                "task_name": f"Research Domain Information: {user_request[:40]}...",
                "category": "Research",
                "required_capability": "web_search",
                "dependencies": [],
                "input_prompt": user_request
            })
            research_dep = [id_research]
        else:
            research_dep = []

        # Step 2: Content Writing / Structure Generation
        if target_output == "comic":
            tasks.append({
                "id": id_write_comic,
                "task_name": "Generate 8-Panel Comic Script & Storyboard (2 Width x 4 Long)",
                "category": "LLM",
                "required_capability": "text",
                "dependencies": research_dep,
                "input_prompt": (
                    f"Create a vibrant color comic strip script for: '{user_request}'.\n"
                    f"Format the comic as exactly 8 panels arranged in a 2-width by 4-long grid (2 columns x 4 rows).\n"
                    f"For each panel (1 to 8), provide: title, visual image prompt description, caption, and dialogue."
                )
            })

            tasks.append({
                "id": id_generate_images,
                "task_name": "Generate Color Comic Panel Visuals",
                "category": "Image Generation",
                "required_capability": "image_generation",
                "dependencies": [id_write_comic],
                "input_prompt": f"Create colorful vibrant comic book illustration panels for: {user_request}"
            })

            tasks.append({
                "id": id_compile_comic,
                "task_name": "Compile 4-Long x 2-Width Color Comic Grid Image & Artifacts",
                "category": "Document Generation",
                "required_capability": "pdf_generation",
                "dependencies": [id_write_comic, id_generate_images],
                "input_prompt": "Compile comic panels into a 2-column by 4-row (2-width x 4-long) color comic strip."
            })

            tasks.append({
                "id": id_quality_review,
                "task_name": "Evaluate & Verify Comic Quality & Grid Layout",
                "category": "Quality Control",
                "required_capability": "quality_review",
                "dependencies": [id_compile_comic],
                "input_prompt": "Evaluate story coherence, color quality, and panel layout."
            })

        elif target_output == "presentation":
            tasks.append({
                "id": id_write_content,
                "task_name": "Generate Presentation Outline & Slide Deck Structure",
                "category": "LLM",
                "required_capability": "text",
                "dependencies": research_dep,
                "input_prompt": (
                    f"Create a detailed 6-to-8 slide presentation structure for: '{user_request}'.\n"
                    f"For each slide provide: title, 3-4 structured bullet points, and a description of a recommended visual image."
                )
            })

            # Step 3: Visual Image Generation (in parallel with writing completion)
            tasks.append({
                "id": id_generate_images,
                "task_name": "Generate Slide Graphics & Visual Illustrations",
                "category": "Image Generation",
                "required_capability": "image_generation",
                "dependencies": [id_write_content],
                "input_prompt": f"Create a high quality visual illustration for: {user_request}"
            })

            # Step 4: Presentation File Compilation
            tasks.append({
                "id": id_compile_pptx,
                "task_name": "Compile PowerPoint Presentation (.pptx)",
                "category": "Presentation Generation",
                "required_capability": "pptx_generation",
                "dependencies": [id_write_content, id_generate_images],
                "input_prompt": "Compile slides and images into PPTX file."
            })

            # Step 5: Quality Review
            tasks.append({
                "id": id_quality_review,
                "task_name": "Evaluate & Verify Presentation Quality",
                "category": "Quality Control",
                "required_capability": "quality_review",
                "dependencies": [id_compile_pptx],
                "input_prompt": "Evaluate completeness and educational value."
            })

        elif target_output in ("document", "report"):
            tasks.append({
                "id": id_write_report,
                "task_name": "Write Detailed Comprehensive Report",
                "category": "LLM",
                "required_capability": "reasoning",
                "dependencies": research_dep,
                "input_prompt": (
                    f"Write an in-depth, structured report on: '{user_request}'.\n"
                    f"Include Executive Summary, Key Analysis, Data Tables, and Conclusion."
                )
            })

            tasks.append({
                "id": id_compile_pdf,
                "task_name": "Compile Format-Ready PDF & DOCX Document",
                "category": "Document Generation",
                "required_capability": "pdf_generation",
                "dependencies": [id_write_report],
                "input_prompt": "Compile structured text into PDF and Word document."
            })

            tasks.append({
                "id": id_quality_review,
                "task_name": "Evaluate & Audit Document Accuracy",
                "category": "Quality Control",
                "required_capability": "quality_review",
                "dependencies": [id_compile_pdf],
                "input_prompt": "Verify factual accuracy and document layout."
            })

        else:  # General Text / Coding / Code generation
            tasks.append({
                "id": id_write_code,
                "task_name": "Generate Code & Technical Implementation",
                "category": "LLM",
                "required_capability": "coding",
                "dependencies": research_dep,
                "input_prompt": f"Generate robust, tested implementation code or solution for: '{user_request}'."
            })

            tasks.append({
                "id": id_quality_review,
                "task_name": "Code Review & Quality Check",
                "category": "Quality Control",
                "required_capability": "quality_review",
                "dependencies": [id_write_code],
                "input_prompt": "Review code for correctness, edge cases, and safety."
            })

        return {
            "title": f"Project: {user_request[:50]}",
            "output_type": target_output,
            "tasks": tasks
        }
