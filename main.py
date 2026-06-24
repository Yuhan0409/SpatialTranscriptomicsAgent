"""
main.py

命令行入口。
用于运行空间转录组分析 Agent。
"""

import argparse
import os

def main():
    parser = argparse.ArgumentParser(
        description="Spatial Transcriptomics Analysis Agent based on LangGraph"
    )

    parser.add_argument(
        "--data",
        type=str,
        required=True,
        help="Path to input .h5ad file",
    )

    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="User natural language query",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="outputs",
        help="Output directory",
    )
    
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM planning and explanation",
    )

    args = parser.parse_args()
    
    if args.no_llm:
        os.environ["OPENAI_API_KEY"] = ""
        os.environ["OPENAI_BASE_URL"] = ""
        os.environ["OPENAI_MODEL"] = ""
        
    from spatial_agent.graph import build_graph

    app = build_graph()

    initial_state = {
        "user_query": args.query,
        "data_path": args.data,
        "output_dir": args.output,

        "plan": [],
        "current_step_index": 0,
        "completed_steps": [],

        "current_data_path": args.data,
        "results": [],
        "figures": [],

        "error": None,
        "retry_count": 0,

        "final_report": "",
        "final_answer": "",
        
        "llm_plan_text": "",
        "llm_explanation": "",
    }

    result = app.invoke(
        initial_state,
        config={"recursion_limit": 50},
    )

    print("\n========== Agent Final Answer ==========")
    print(result["final_answer"])

    print("\n========== Generated Figures ==========")
    for fig in result["figures"]:
        print(fig)

    print("\n========== Report ==========")
    print(result["final_report"])

if __name__ == "__main__":
    main()