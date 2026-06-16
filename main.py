#!/usr/bin/env python3
import argparse
import sys
import os
import json
import config
import orchestrator

def list_templates():
    """
    List available roundtable templates.
    """
    if not os.path.exists(config.TEMPLATES_DIR):
        print("No templates directory found.")
        return
        
    print("\nAvailable StockPartner templates:")
    print("=================================")
    for d in os.listdir(config.TEMPLATES_DIR):
        tpath = os.path.join(config.TEMPLATES_DIR, d)
        cfg_path = os.path.join(tpath, "config.json")
        if os.path.isdir(tpath) and os.path.exists(cfg_path):
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                name = cfg.get("name", d)
                desc = cfg.get("description", "No description")
                print(f"- {name}: {desc}")
            except Exception as e:
                print(f"- {d}: Error reading config.json ({e})")
    print("=================================\n")

def load_template_query(template_name):
    """
    Loads query from the given template config.json.
    """
    tpath = os.path.join(config.TEMPLATES_DIR, template_name)
    cfg_path = os.path.join(tpath, "config.json")
    if not os.path.exists(cfg_path):
        print(f"Error: Template config not found at {cfg_path}", file=sys.stderr)
        sys.exit(1)
        
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
        
    # We can extract the query from one of the members prompts or descriptions
    # Let's check config.json members prompts
    members = cfg.get("members", [])
    query = ""
    for member in members:
        prompt = member.get("prompt", "")
        # Extract user query using regex: 用户问题：xxx
        m = re.search(r"用户问题[：:](.*?)(?:\n|$)", prompt)
        if m:
            query = m.group(1).strip()
            break
            
    if not query:
        # Fallback to description
        query = cfg.get("description", "")
        
    return query

def main():
    parser = argparse.ArgumentParser(description="StockPartner Multi-Agent Roundtable Orchestrator")
    
    # Execution arguments
    parser.add_argument("--query", help="The analysis query to run (e.g. '分析贵州茅台走势')")
    parser.add_argument("--code", help="Comma-separated stock codes (e.g. 'sh600519,hk00700')")
    
    # Template arguments
    parser.add_argument("--template", help="Run using a pre-defined roundtable template query")
    parser.add_argument("--list-templates", action="store_true", help="List all available templates and exit")
    
    # Extra tuning
    parser.add_argument("--agents", help="Comma-separated list of sub-agent IDs to activate (e.g. 'valuation-analyst,signal-chief')")
    parser.add_argument("--output", help="Custom output directory for saved reports")
    
    args = parser.parse_args()
    
    if args.list_templates:
        list_templates()
        sys.exit(0)
        
    # Determine the query to run
    query = ""
    if args.template:
        import re # Import here for query extraction regex
        print(f"[*] Loading query from template: {args.template}")
        query = load_template_query(args.template)
        if args.code:
            query += f" (股票代码: {args.code})"
    elif args.query:
        query = args.query
        if args.code:
            query += f" (股票代码: {args.code})"
    else:
        parser.print_help()
        print("\nError: Please specify either --query or --template to run, or --list-templates to list available templates.", file=sys.stderr)
        sys.exit(1)
        
    # Determine which agents to run
    active_agents = None
    if args.agents:
        active_agents = [a.strip() for a in args.agents.split(",") if a.strip()]
        
    # Run the orchestrator
    try:
        results = orchestrator.run_team_roundtable(
            user_query=query,
            active_agents=active_agents,
            output_dir=args.output
        )
        
        print("\n" + "="*50)
        print("Roundtable Analysis Completed successfully!")
        print("="*50)
        print(f"[*] Reports saved to directory: {results['output_dir']}")
        print(f"[*] Lead report (Markdown): {results['md_report']}")
        if results['html_report']:
            print(f"[*] Lead report (HTML): {results['html_report']}")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"\nExecution failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
