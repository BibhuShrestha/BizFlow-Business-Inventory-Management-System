"""
AI Business Analytics and Decision Support Integration.

Architecture:
- Resource-efficient, storage-efficient, lightweight hybrid architecture.
- Deterministic Local Decision Advisor runs with zero network latency, zero token cost,
  and zero external dependencies.
- Optional external AI provider (Gemini / OpenAI compatible) invoked only on-demand
  with compact, anonymized aggregated summaries (< 350 tokens).
- Bounded in-memory / Django caching prevents duplicate API calls.
"""
import hashlib
import json
import logging
import os
import time
from typing import Any

from django.core.cache import cache

logger = logging.getLogger("bizflow.ai_analytics")


class LocalDeterministicAdvisor:
    """
    Lightweight, deterministic decision support engine.
    Produces structured business recommendations using mathematical financial ratios,
    inventory velocity, and debt aging rules without any external AI API latency or cost.
    """

    @classmethod
    def generate_insights(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Generate structured business advice based on deterministic business rules."""
        revenue = float(data.get("revenue", 0.0))
        net_profit = float(data.get("net_profit", 0.0))
        margin_pct = float(data.get("net_margin_pct", 0.0))
        receivables_overdue = float(data.get("receivables_overdue", 0.0))
        receivables_total = float(data.get("receivables_total", 0.0))
        payables_total = float(data.get("payables_total", 0.0))
        low_stock_count = int(data.get("low_stock_count", 0))
        out_of_stock_count = int(data.get("out_of_stock_count", 0))
        health_score = int(data.get("health_score", 75))

        # 1. Executive Summary
        if revenue == 0:
            summary = "Business operations are in the setup or low-volume phase. Focus on initial sales generation and inventory positioning."
        elif margin_pct >= 20.0 and receivables_overdue < (revenue * 0.1):
            summary = f"Strong financial health ({health_score}/100) with robust {margin_pct:.1f}% net margins and controlled customer credit risk."
        elif margin_pct < 5.0 or net_profit < 0:
            summary = f"Compressed profitability ({margin_pct:.1f}% net margin). Operational overhead or cost of sales requires immediate cost containment."
        else:
            summary = f"Steady operational performance ({health_score}/100). Maintain sales velocity while addressing working capital and inventory reorder priorities."

        # 2. Strategic Action Plan (Priority Actions)
        actions = []
        if out_of_stock_count > 0:
            actions.append({
                "category": "Inventory",
                "priority": "High",
                "title": f"Restock {out_of_stock_count} depleted item(s)",
                "detail": "Completely out-of-stock products cause immediate lost sales. Review supplier purchase orders."
            })
        elif low_stock_count > 0:
            actions.append({
                "category": "Inventory",
                "priority": "Medium",
                "title": f"Reorder {low_stock_count} low-stock product(s)",
                "detail": "Current inventory is below minimum safety thresholds. Place vendor replenishment orders."
            })

        if receivables_overdue > 0:
            actions.append({
                "category": "Credit & Cashflow",
                "priority": "High",
                "title": f"Recover Rs. {receivables_overdue:,.2f} in overdue receivables",
                "detail": "Customer debt has exceeded payment due dates. Issue SMS payment reminders and restrict further credit sales."
            })

        if payables_total > receivables_total and receivables_total > 0:
            actions.append({
                "category": "Working Capital",
                "priority": "Medium",
                "title": "Vendor Payables exceed Customer Receivables",
                "detail": f"Supplier liabilities (Rs. {payables_total:,.2f}) exceed receivables (Rs. {receivables_total:,.2f}). Manage payment schedules to preserve cash liquidity."
            })

        top_expenses = data.get("top_expense_categories", [])
        if top_expenses:
            top_exp = top_expenses[0]
            actions.append({
                "category": "Cost Control",
                "priority": "Low",
                "title": f"Monitor '{top_exp.get('category')}' overhead",
                "detail": f"Leading operational expense category totaling Rs. {float(top_exp.get('amount', 0)):,.2f} ({top_exp.get('percentage', 0):.1f}% of expenses)."
            })

        if not actions:
            actions.append({
                "category": "Growth",
                "priority": "Low",
                "title": "Capitalize on high-margin product expansion",
                "detail": "Current financial and stock indicators are balanced. Explore volume purchase discounts with key suppliers."
            })

        # 3. Working Capital & Cashflow Outlook
        working_cap = float(data.get("working_capital_net", 0.0))
        if working_cap >= 0:
            cashflow_outlook = f"Positive working capital buffer of Rs. {working_cap:,.2f}. Short-term obligations are covered by active trade receivables."
        else:
            cashflow_outlook = f"Working capital deficit of Rs. {abs(working_cap):,.2f}. Prioritize collecting customer dues before liquidating vendor trade payables."

        # 4. Growth & Merchandising Opportunities
        fast_moving = data.get("fast_moving_products", [])
        if fast_moving:
            top_prod = fast_moving[0].get("name", "Leading item")
            growth_tip = f"Boost stock allocation for '{top_prod}', which generated the highest sales velocity this period."
        else:
            growth_tip = "Expand marketing outreach to create recurring product sales demand."

        return {
            "source": "local_rules",
            "provider": "BizFlow Deterministic Engine",
            "model": "Rules-v2.1",
            "health_score": health_score,
            "executive_summary": summary,
            "action_plan": actions,
            "cashflow_outlook": cashflow_outlook,
            "growth_opportunities": growth_tip,
            "timestamp": time.time(),
        }


class AIAnalyticsService:
    """
    Hybrid AI Business Analytics Service.
    - Anonymized compact JSON summary (< 350 tokens).
    - Checks cache before firing external calls.
    - Calls Gemini API / OpenAI compatible REST API if API key is configured.
    - Gracefully falls back to LocalDeterministicAdvisor on failure, timeout, or missing key.
    """

    CACHE_TTL_SECONDS = 3600  # 1 hour bounded cache
    RATE_LIMIT_PER_HOUR = 15  # Max 15 AI requests per user/company per hour

    @classmethod
    def _compute_cache_key(cls, company_id: int | None, data: dict[str, Any]) -> str:
        """Generate a deterministic cache key from company ID and core figures."""
        signature = f"{company_id}_{data.get('revenue')}_{data.get('net_profit')}_{data.get('receivables_total')}_{data.get('low_stock_count')}"
        digest = hashlib.md5(signature.encode("utf-8")).hexdigest()[:12]
        return f"bizflow_ai_insights_{company_id or 'global'}_{digest}"

    @classmethod
    def get_insights(
        cls,
        summary_data: dict[str, Any],
        company_id: int | None = None,
        force_refresh: bool = False,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Retrieve AI-powered business analytics.
        Returns cached insights, live AI generation, or deterministic local fallback.
        """
        cache_key = cls._compute_cache_key(company_id, summary_data)

        if not force_refresh:
            cached_result = cache.get(cache_key)
            if cached_result:
                cached_result["source"] = "cache"
                return cached_result

        # User rate limit check
        if user_id:
            user_rate_key = f"bizflow_ai_rate_{user_id}_{time.strftime('%Y%m%d%H')}"
            current_count = cache.get(user_rate_key, 0)
            if current_count >= cls.RATE_LIMIT_PER_HOUR:
                logger.warning("User %s exceeded AI analytics rate limit", user_id)
                fallback = LocalDeterministicAdvisor.generate_insights(summary_data)
                fallback["rate_limited"] = True
                fallback["rate_limit_message"] = "Hourly AI quota reached (15/hr). Serving deterministic local engine advice."
                return fallback
            cache.set(user_rate_key, current_count + 1, timeout=3600)

        # Check for configured API Key
        gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("AI_API_KEY")
        if not gemini_api_key:
            # No external key configured -> instant local rules
            result = LocalDeterministicAdvisor.generate_insights(summary_data)
            cache.set(cache_key, result, timeout=cls.CACHE_TTL_SECONDS)
            return result

        # Attempt compact AI Call
        try:
            ai_result = cls._call_gemini_api(gemini_api_key, summary_data)
            if ai_result:
                cache.set(cache_key, ai_result, timeout=cls.CACHE_TTL_SECONDS)
                return ai_result
        except Exception as exc:
            logger.warning("External AI API call failed (%s). Falling back to local engine.", exc)

        # Fallback on any failure
        fallback = LocalDeterministicAdvisor.generate_insights(summary_data)
        fallback["source"] = "local_rules_fallback"
        cache.set(cache_key, fallback, timeout=cls.CACHE_TTL_SECONDS)
        return fallback

    @classmethod
    def _call_gemini_api(cls, api_key: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Call Gemini Flash API with compact anonymized JSON prompt."""
        import httpx

        # Compact anonymized summary - zero customer names or individual order rows
        compact_payload = {
            "period": f"{data.get('period_days', 30)} days",
            "revenue_npr": float(data.get("revenue", 0)),
            "cost_of_goods_npr": float(data.get("purchases", 0)),
            "expenses_npr": float(data.get("expenses", 0)),
            "net_profit_npr": float(data.get("net_profit", 0)),
            "net_margin_pct": float(data.get("net_margin_pct", 0)),
            "receivables_due_npr": float(data.get("receivables_total", 0)),
            "receivables_overdue_npr": float(data.get("receivables_overdue", 0)),
            "payables_due_npr": float(data.get("payables_total", 0)),
            "low_stock_sku_count": int(data.get("low_stock_count", 0)),
            "out_of_stock_sku_count": int(data.get("out_of_stock_count", 0)),
            "top_products": [p.get("name") for p in data.get("fast_moving_products", [])[:3]],
        }

        prompt = (
            "You are a seasoned CFO and business inventory consultant for a retail/wholesale SME in Nepal. "
            "Analyze the following compact business summary and return ONLY a valid JSON object matching this schema:\n"
            "{\n"
            '  "health_score": <integer 0-100>,\n'
            '  "executive_summary": "<2-sentence clear diagnosis>",\n'
            '  "action_plan": [\n'
            '     {"category": "<Inventory|Credit|Cost|Growth>", "priority": "<High|Medium|Low>", "title": "<short title>", "detail": "<actionable advice>"}\n'
            "  ],\n"
            '  "cashflow_outlook": "<1-2 sentence working capital commentary>",\n'
            '  "growth_opportunities": "<1-2 sentence recommendation on fast-moving items or margin enhancement>"\n'
            "}\n\n"
            f"Business Summary Data:\n{json.dumps(compact_payload)}"
        )

        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 600,
                "responseMimeType": "application/json"
            }
        }

        with httpx.Client(timeout=8.0) as client:
            resp = client.post(url, json=body)
            if resp.status_code != 200:
                logger.warning("Gemini API error status %s: %s", resp.status_code, resp.text[:200])
                return None

            resp_json = resp.json()
            candidates = resp_json.get("candidates", [])
            if not candidates:
                return None

            content_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            if not content_text:
                return None

            # Parse JSON response
            parsed = json.loads(content_text.strip().removeprefix("```json").removesuffix("```").strip())
            return {
                "source": "ai_live",
                "provider": "Google Gemini",
                "model": model_name,
                "health_score": parsed.get("health_score", data.get("health_score", 75)),
                "executive_summary": parsed.get("executive_summary", ""),
                "action_plan": parsed.get("action_plan", []),
                "cashflow_outlook": parsed.get("cashflow_outlook", ""),
                "growth_opportunities": parsed.get("growth_opportunities", ""),
                "timestamp": time.time(),
            }
