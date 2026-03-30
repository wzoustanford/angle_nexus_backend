#!/usr/bin/env python3
"""
Bandwidth Analysis Tool

Analyze historical bandwidth consumption logs and generate insights.

Usage:
    python analyze_bandwidth.py                    # Analyze last 7 days
    python analyze_bandwidth.py --days 30          # Analyze last 30 days
    python analyze_bandwidth.py --compare baseline.json  # Compare with baseline
"""

import argparse
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


def format_bytes(bytes_val):
    """Format bytes into human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:6.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:6.2f} TB"


def load_metrics_files(log_dir, days=None):
    """Load metrics files from log directory."""
    log_path = Path(log_dir)
    if not log_path.exists():
        print(f"❌ Log directory not found: {log_dir}")
        return []
    
    metrics_files = sorted(log_path.glob('metrics_*.json'))
    
    if not metrics_files:
        print("❌ No metrics files found")
        return []
    
    if days:
        # Filter by date
        cutoff_date = datetime.now() - timedelta(days=days)
        metrics_files = [
            f for f in metrics_files 
            if datetime.strptime(f.stem.split('_')[1], '%Y%m%d') > cutoff_date
        ]
    
    return metrics_files


def analyze_trends(log_dir='./logs/bandwidth', days=7):
    """Analyze bandwidth trends over time."""
    metrics_files = load_metrics_files(log_dir, days)
    
    if not metrics_files:
        return
    
    print("\n" + "=" * 100)
    print(f"📊 BANDWIDTH TREND ANALYSIS (Last {len(metrics_files)} sessions)")
    print("=" * 100)
    
    daily_data = []
    total_bandwidth = 0
    total_calls = 0
    
    for metrics_file in metrics_files:
        with open(metrics_file, 'r') as f:
            data = json.load(f)
            session = data['session']
            
            date_str = session['session_id'][:8]
            date = datetime.strptime(date_str, '%Y%m%d')
            
            daily_data.append({
                'date': date,
                'date_str': date.strftime('%Y-%m-%d'),
                'bandwidth': session['total_bandwidth'],
                'calls': session['api_calls'],
                'cache_hits': session['cache_hits'],
                'cache_hit_rate': float(session['cache_hit_rate'].rstrip('%')),
                'tickers_updated': session['tickers_updated'],
                'tickers_skipped': session['tickers_skipped']
            })
            
            total_bandwidth += session['total_bandwidth']
            total_calls += session['api_calls']
    
    # Calculate statistics
    avg_bandwidth = total_bandwidth / len(daily_data)
    bandwidths = [d['bandwidth'] for d in daily_data]
    min_bandwidth = min(bandwidths)
    max_bandwidth = max(bandwidths)
    
    print(f"\n📈 SUMMARY STATISTICS")
    print("-" * 100)
    print(f"Total Bandwidth:        {format_bytes(total_bandwidth)}")
    print(f"Average per Session:    {format_bytes(avg_bandwidth)}")
    print(f"Minimum:                {format_bytes(min_bandwidth)}")
    print(f"Maximum:                {format_bytes(max_bandwidth)}")
    print(f"Total API Calls:        {total_calls:,}")
    print(f"Average Calls per Day:  {total_calls / len(daily_data):.0f}")
    
    # Daily breakdown
    print(f"\n📅 DAILY BREAKDOWN")
    print("-" * 100)
    print(f"{'Date':12s} | {'Bandwidth':>14s} | {'API Calls':>10s} | {'Cache Rate':>10s} | "
          f"{'Updated':>8s} | {'Skipped':>8s}")
    print("-" * 100)
    
    for data in daily_data:
        print(
            f"{data['date_str']:12s} | "
            f"{format_bytes(data['bandwidth']):>14s} | "
            f"{data['calls']:>10,d} | "
            f"{data['cache_hit_rate']:>9.1f}% | "
            f"{data['tickers_updated']:>8,d} | "
            f"{data['tickers_skipped']:>8,d}"
        )
    
    # Trend analysis
    print(f"\n📉 TREND ANALYSIS")
    print("-" * 100)
    
    if len(daily_data) >= 2:
        first_day = daily_data[0]
        last_day = daily_data[-1]
        
        bandwidth_change = last_day['bandwidth'] - first_day['bandwidth']
        bandwidth_change_pct = (bandwidth_change / first_day['bandwidth']) * 100
        
        cache_rate_change = last_day['cache_hit_rate'] - first_day['cache_hit_rate']
        
        print(f"Bandwidth Trend:        {format_bytes(bandwidth_change)} ({bandwidth_change_pct:+.1f}%)")
        print(f"Cache Hit Rate Trend:   {cache_rate_change:+.1f}%")
        
        if bandwidth_change < 0:
            print(f"✅ Optimization working! Bandwidth decreased by {format_bytes(abs(bandwidth_change))}")
        else:
            print(f"⚠️  Bandwidth increased. Check for data growth or optimization issues.")
    
    # Cost analysis
    print(f"\n💰 COST ANALYSIS (AWS Data Transfer @ $0.09/GB)")
    print("-" * 100)
    
    cost_per_gb = 0.09
    total_gb = total_bandwidth / (1024**3)
    est_monthly_cost = (avg_bandwidth / (1024**3)) * 30 * cost_per_gb
    est_yearly_cost = est_monthly_cost * 12
    
    print(f"Total Cost (period):    ${total_gb * cost_per_gb:.2f}")
    print(f"Est. Monthly Cost:      ${est_monthly_cost:.2f}")
    print(f"Est. Yearly Cost:       ${est_yearly_cost:.2f}")
    
    # Savings estimate (compare first day vs average of rest)
    if len(daily_data) > 1:
        baseline = daily_data[0]['bandwidth']
        optimized_avg = sum(d['bandwidth'] for d in daily_data[1:]) / (len(daily_data) - 1)
        savings_per_day = baseline - optimized_avg
        
        if savings_per_day > 0:
            savings_pct = (savings_per_day / baseline) * 100
            monthly_savings = (savings_per_day / (1024**3)) * 30 * cost_per_gb
            yearly_savings = monthly_savings * 12
            
            print(f"\n💾 OPTIMIZATION SAVINGS")
            print("-" * 100)
            print(f"Baseline (Day 1):       {format_bytes(baseline)}")
            print(f"Average (Optimized):    {format_bytes(optimized_avg)}")
            print(f"Savings per Day:        {format_bytes(savings_per_day)} ({savings_pct:.1f}%)")
            print(f"Est. Monthly Savings:   ${monthly_savings:.2f}")
            print(f"Est. Yearly Savings:    ${yearly_savings:.2f}")
    
    print("\n" + "=" * 100 + "\n")


def compare_sessions(session1_file, session2_file):
    """Compare two bandwidth monitoring sessions."""
    with open(session1_file, 'r') as f:
        session1 = json.load(f)
    
    with open(session2_file, 'r') as f:
        session2 = json.load(f)
    
    s1 = session1['session']
    s2 = session2['session']
    
    print("\n" + "=" * 100)
    print("🔄 SESSION COMPARISON")
    print("=" * 100)
    
    print(f"\nSession 1: {session1_file.name}")
    print(f"Session 2: {session2_file.name}")
    print("")
    
    print(f"{'Metric':<30s} | {'Session 1':>15s} | {'Session 2':>15s} | {'Change':>20s}")
    print("-" * 100)
    
    # Bandwidth
    bw_change = s2['total_bandwidth'] - s1['total_bandwidth']
    bw_change_pct = (bw_change / s1['total_bandwidth']) * 100
    print(f"{'Bandwidth':<30s} | {format_bytes(s1['total_bandwidth']):>15s} | "
          f"{format_bytes(s2['total_bandwidth']):>15s} | "
          f"{format_bytes(bw_change):>12s} ({bw_change_pct:+6.1f}%)")
    
    # API Calls
    call_change = s2['api_calls'] - s1['api_calls']
    call_change_pct = (call_change / max(1, s1['api_calls'])) * 100
    print(f"{'API Calls':<30s} | {s1['api_calls']:>15,d} | {s2['api_calls']:>15,d} | "
          f"{call_change:>+12,d} ({call_change_pct:+6.1f}%)")
    
    # Cache Hit Rate
    chr1 = float(s1['cache_hit_rate'].rstrip('%'))
    chr2 = float(s2['cache_hit_rate'].rstrip('%'))
    chr_change = chr2 - chr1
    print(f"{'Cache Hit Rate':<30s} | {s1['cache_hit_rate']:>15s} | "
          f"{s2['cache_hit_rate']:>15s} | {chr_change:>+18.1f}%")
    
    # Tickers
    tu_change = s2['tickers_updated'] - s1['tickers_updated']
    print(f"{'Tickers Updated':<30s} | {s1['tickers_updated']:>15,d} | "
          f"{s2['tickers_updated']:>15,d} | {tu_change:>+19,d}")
    
    ts_change = s2['tickers_skipped'] - s1['tickers_skipped']
    print(f"{'Tickers Skipped':<30s} | {s1['tickers_skipped']:>15,d} | "
          f"{s2['tickers_skipped']:>15,d} | {ts_change:>+19,d}")
    
    print("\n" + "=" * 100 + "\n")


def generate_optimization_score(log_dir='./logs/bandwidth'):
    """Generate an optimization effectiveness score."""
    metrics_files = load_metrics_files(log_dir)
    
    if len(metrics_files) < 2:
        print("❌ Need at least 2 sessions to calculate optimization score")
        return
    
    # First session is baseline, calculate average of rest
    with open(metrics_files[0], 'r') as f:
        baseline = json.load(f)['session']
    
    optimized_sessions = []
    for mf in metrics_files[1:]:
        with open(mf, 'r') as f:
            optimized_sessions.append(json.load(f)['session'])
    
    avg_optimized_bandwidth = sum(s['total_bandwidth'] for s in optimized_sessions) / len(optimized_sessions)
    avg_cache_rate = sum(float(s['cache_hit_rate'].rstrip('%')) for s in optimized_sessions) / len(optimized_sessions)
    
    # Calculate score (0-100)
    bandwidth_reduction = ((baseline['total_bandwidth'] - avg_optimized_bandwidth) / 
                          baseline['total_bandwidth']) * 100
    
    # Score components
    bandwidth_score = min(50, bandwidth_reduction * 0.625)  # Max 50 points (80% reduction)
    cache_score = min(30, avg_cache_rate * 0.375)  # Max 30 points (80% cache rate)
    consistency_score = 20 if len(optimized_sessions) >= 3 else 10  # Consistency bonus
    
    total_score = bandwidth_score + cache_score + consistency_score
    
    print("\n" + "=" * 100)
    print("🎯 OPTIMIZATION EFFECTIVENESS SCORE")
    print("=" * 100)
    print(f"\nBandwidth Reduction:    {bandwidth_reduction:.1f}% → {bandwidth_score:.0f}/50 points")
    print(f"Cache Hit Rate:         {avg_cache_rate:.1f}% → {cache_score:.0f}/30 points")
    print(f"Consistency:            {len(optimized_sessions)} sessions → {consistency_score}/20 points")
    print(f"\n{'TOTAL SCORE':>20s}: {total_score:.0f}/100")
    
    if total_score >= 80:
        grade = "🏆 EXCELLENT"
    elif total_score >= 60:
        grade = "✅ GOOD"
    elif total_score >= 40:
        grade = "⚠️  FAIR"
    else:
        grade = "❌ NEEDS IMPROVEMENT"
    
    print(f"{'GRADE':>20s}: {grade}")
    print("\n" + "=" * 100 + "\n")


def main():
    parser = argparse.ArgumentParser(description='Analyze bandwidth consumption logs')
    parser.add_argument('--days', type=int, default=7, help='Number of days to analyze')
    parser.add_argument('--log-dir', default='./logs/bandwidth', help='Log directory path')
    parser.add_argument('--compare', nargs=2, metavar=('FILE1', 'FILE2'), 
                       help='Compare two metrics files')
    parser.add_argument('--score', action='store_true', 
                       help='Generate optimization effectiveness score')
    
    args = parser.parse_args()
    
    if args.compare:
        compare_sessions(Path(args.compare[0]), Path(args.compare[1]))
    elif args.score:
        generate_optimization_score(args.log_dir)
    else:
        analyze_trends(args.log_dir, args.days)


if __name__ == '__main__':
    main()
