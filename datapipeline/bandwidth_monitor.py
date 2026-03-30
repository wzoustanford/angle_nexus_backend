"""
Bandwidth Monitoring and Reporting Module
Tracks data consumption, API calls, and generates usage reports.

Usage:
    from bandwidth_monitor import BandwidthMonitor
    
    monitor = BandwidthMonitor()
    monitor.log_api_call('AAPL', 'historical-price-full', request_size=500, response_size=15000)
    monitor.log_cache_hit('MSFT', 'profile')
    monitor.generate_daily_report()
"""

import os
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path


class BandwidthMonitor:
    """Monitor and log bandwidth consumption with detailed reporting."""
    
    def __init__(self, log_dir='./logs/bandwidth'):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Current session tracking
        self.session_start = datetime.now()
        self.session_id = self.session_start.strftime("%Y%m%d_%H%M%S")
        
        # Metrics tracking
        self.total_bytes = 0
        self.api_calls = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.skipped_tickers = 0
        self.updated_tickers = 0
        
        # Detailed breakdown
        self.category_stats = defaultdict(lambda: {'bytes': 0, 'calls': 0})
        self.ticker_stats = defaultdict(lambda: {'bytes': 0, 'calls': 0, 'cached': 0})
        self.hourly_stats = defaultdict(lambda: {'bytes': 0, 'calls': 0})
        
        # Initialize logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup dedicated bandwidth logging."""
        log_file = self.log_dir / f'bandwidth_{self.session_id}.log'
        
        self.logger = logging.getLogger('bandwidth_monitor')
        self.logger.setLevel(logging.INFO)
        
        # File handler
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        
        self.logger.info(f"=== Bandwidth Monitoring Session Started: {self.session_id} ===")
        
    def log_api_call(self, ticker, category, request_size=0, response_size=0, 
                     is_incremental=False, records_fetched=0):
        """
        Log an API call with bandwidth details.
        
        Args:
            ticker: Stock symbol
            category: API category (e.g., 'historical-price-full', 'profile')
            request_size: Size of request in bytes
            response_size: Size of response in bytes
            is_incremental: Whether this was an incremental fetch
            records_fetched: Number of records returned
        """
        total_bytes = request_size + response_size + 500  # +500 for headers
        self.total_bytes += total_bytes
        self.api_calls += 1
        self.cache_misses += 1
        
        # Update category stats
        self.category_stats[category]['bytes'] += total_bytes
        self.category_stats[category]['calls'] += 1
        
        # Update ticker stats
        self.ticker_stats[ticker]['bytes'] += total_bytes
        self.ticker_stats[ticker]['calls'] += 1
        
        # Update hourly stats
        hour = datetime.now().strftime("%Y-%m-%d %H:00")
        self.hourly_stats[hour]['bytes'] += total_bytes
        self.hourly_stats[hour]['calls'] += 1
        
        # Log details
        fetch_type = "INCREMENTAL" if is_incremental else "FULL"
        self.logger.info(
            f"API_CALL | {ticker:6s} | {category:30s} | "
            f"{fetch_type:12s} | {self._format_bytes(total_bytes):>10s} | "
            f"Records: {records_fetched:>6d}"
        )
        
    def log_cache_hit(self, ticker, category, reason="cached"):
        """
        Log a cache hit (data not fetched).
        
        Args:
            ticker: Stock symbol
            category: API category that was cached
            reason: Why it was cached (e.g., 'up-to-date', 'fresh', 'weekend')
        """
        self.cache_hits += 1
        self.ticker_stats[ticker]['cached'] += 1
        
        self.logger.info(
            f"CACHE_HIT | {ticker:6s} | {category:30s} | "
            f"Reason: {reason:20s} | Bandwidth saved"
        )
        
    def log_ticker_skipped(self, ticker, reason="up-to-date"):
        """Log when a ticker is completely skipped."""
        self.skipped_tickers += 1
        self.logger.info(f"SKIPPED   | {ticker:6s} | {reason}")
        
    def log_ticker_updated(self, ticker, bytes_consumed=0):
        """Log when a ticker is updated."""
        self.updated_tickers += 1
        if bytes_consumed > 0:
            self.logger.info(
                f"UPDATED   | {ticker:6s} | {self._format_bytes(bytes_consumed)}"
            )
    
    def log_optimization_event(self, event_type, details):
        """
        Log bandwidth optimization events.
        
        Args:
            event_type: Type of optimization (e.g., 'incremental_fetch', 'weekend_skip')
            details: Dictionary with event details
        """
        self.logger.info(f"OPTIMIZATION | {event_type:20s} | {details}")
        
    def _format_bytes(self, bytes_val):
        """Format bytes into human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:6.2f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:6.2f} TB"
    
    def get_current_stats(self):
        """Get current session statistics."""
        duration = (datetime.now() - self.session_start).total_seconds()
        
        return {
            'session_id': self.session_id,
            'duration_seconds': duration,
            'total_bandwidth': self.total_bytes,
            'total_bandwidth_formatted': self._format_bytes(self.total_bytes),
            'api_calls': self.api_calls,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': f"{(self.cache_hits / max(1, self.cache_hits + self.cache_misses)) * 100:.1f}%",
            'tickers_updated': self.updated_tickers,
            'tickers_skipped': self.skipped_tickers,
            'avg_bandwidth_per_call': self.total_bytes / max(1, self.api_calls),
        }
    
    def generate_daily_report(self):
        """Generate comprehensive daily bandwidth report."""
        stats = self.get_current_stats()
        duration_mins = stats['duration_seconds'] / 60
        
        report_file = self.log_dir / f'report_{self.session_id}.txt'
        
        report = []
        report.append("=" * 80)
        report.append(f"BANDWIDTH CONSUMPTION REPORT")
        report.append(f"Session: {self.session_id}")
        report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        report.append("")
        
        # Overview
        report.append("📊 OVERVIEW")
        report.append("-" * 80)
        report.append(f"Total Bandwidth:        {stats['total_bandwidth_formatted']}")
        report.append(f"Duration:               {duration_mins:.1f} minutes")
        report.append(f"Total API Calls:        {stats['api_calls']:,}")
        report.append(f"Cache Hits:             {stats['cache_hits']:,}")
        report.append(f"Cache Hit Rate:         {stats['cache_hit_rate']}")
        report.append(f"Tickers Updated:        {stats['tickers_updated']:,}")
        report.append(f"Tickers Skipped:        {stats['tickers_skipped']:,}")
        report.append("")
        
        # Bandwidth by category
        report.append("📁 BANDWIDTH BY CATEGORY")
        report.append("-" * 80)
        sorted_categories = sorted(
            self.category_stats.items(),
            key=lambda x: x[1]['bytes'],
            reverse=True
        )
        for category, stats_dict in sorted_categories[:10]:
            pct = (stats_dict['bytes'] / max(1, self.total_bytes)) * 100
            report.append(
                f"{category:35s} | "
                f"{self._format_bytes(stats_dict['bytes']):>12s} | "
                f"{stats_dict['calls']:>6d} calls | "
                f"{pct:>5.1f}%"
            )
        report.append("")
        
        # Top bandwidth consumers (tickers)
        report.append("🔝 TOP 20 BANDWIDTH CONSUMERS (Tickers)")
        report.append("-" * 80)
        sorted_tickers = sorted(
            self.ticker_stats.items(),
            key=lambda x: x[1]['bytes'],
            reverse=True
        )
        for ticker, stats_dict in sorted_tickers[:20]:
            report.append(
                f"{ticker:8s} | "
                f"{self._format_bytes(stats_dict['bytes']):>12s} | "
                f"{stats_dict['calls']:>4d} calls | "
                f"{stats_dict['cached']:>4d} cached"
            )
        report.append("")
        
        # Hourly breakdown
        report.append("⏰ HOURLY BREAKDOWN")
        report.append("-" * 80)
        sorted_hours = sorted(self.hourly_stats.items())
        for hour, stats_dict in sorted_hours:
            report.append(
                f"{hour} | "
                f"{self._format_bytes(stats_dict['bytes']):>12s} | "
                f"{stats_dict['calls']:>6d} calls"
            )
        report.append("")
        
        # Savings estimate (if historical data available)
        report.append("💰 ESTIMATED SAVINGS")
        report.append("-" * 80)
        
        # Calculate savings based on cache hits
        estimated_saved_bytes = self.cache_hits * 50000  # Assume 50KB per cached call
        total_without_opt = self.total_bytes + estimated_saved_bytes
        saved_pct = (estimated_saved_bytes / max(1, total_without_opt)) * 100
        
        report.append(f"Bandwidth Used:         {self._format_bytes(self.total_bytes)}")
        report.append(f"Bandwidth Saved (est):  {self._format_bytes(estimated_saved_bytes)}")
        report.append(f"Total w/o Optimization: {self._format_bytes(total_without_opt)}")
        report.append(f"Reduction:              {saved_pct:.1f}%")
        report.append("")
        
        # Cost estimate
        cost_per_gb = 0.09  # AWS data transfer cost
        cost_actual = (self.total_bytes / (1024**3)) * cost_per_gb
        cost_without = (total_without_opt / (1024**3)) * cost_per_gb
        cost_saved = cost_without - cost_actual
        
        report.append(f"Actual Cost (est):      ${cost_actual:.2f}")
        report.append(f"Cost w/o Optimization:  ${cost_without:.2f}")
        report.append(f"Cost Saved:             ${cost_saved:.2f}")
        report.append("")
        
        report.append("=" * 80)
        report.append(f"Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        
        # Write to file
        report_text = "\n".join(report)
        with open(report_file, 'w') as f:
            f.write(report_text)
        
        # Also log to console
        print("\n" + report_text)
        
        self.logger.info(f"Report generated: {report_file}")
        
        return report_text
    
    def save_metrics_json(self):
        """Save metrics as JSON for programmatic access."""
        metrics_file = self.log_dir / f'metrics_{self.session_id}.json'
        
        metrics = {
            'session': self.get_current_stats(),
            'categories': dict(self.category_stats),
            'top_tickers': dict(sorted(
                self.ticker_stats.items(),
                key=lambda x: x[1]['bytes'],
                reverse=True
            )[:50]),
            'hourly': dict(self.hourly_stats)
        }
        
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        self.logger.info(f"Metrics saved: {metrics_file}")
        return metrics_file
    
    def compare_with_baseline(self, baseline_file):
        """
        Compare current session with a baseline report.
        
        Args:
            baseline_file: Path to baseline metrics JSON file
        """
        if not os.path.exists(baseline_file):
            self.logger.warning(f"Baseline file not found: {baseline_file}")
            return None
        
        with open(baseline_file, 'r') as f:
            baseline = json.load(f)
        
        current = self.get_current_stats()
        
        comparison = {
            'bandwidth_change': current['total_bandwidth'] - baseline['session']['total_bandwidth'],
            'bandwidth_change_pct': (
                (current['total_bandwidth'] - baseline['session']['total_bandwidth']) / 
                max(1, baseline['session']['total_bandwidth'])
            ) * 100,
            'api_calls_change': current['api_calls'] - baseline['session']['api_calls'],
            'cache_hit_rate_change': (
                float(current['cache_hit_rate'].rstrip('%')) - 
                float(baseline['session']['cache_hit_rate'].rstrip('%'))
            ),
        }
        
        # Print comparison
        print("\n" + "=" * 80)
        print("📊 COMPARISON WITH BASELINE")
        print("=" * 80)
        print(f"Bandwidth Change:   {self._format_bytes(comparison['bandwidth_change']):>12s} "
              f"({comparison['bandwidth_change_pct']:+.1f}%)")
        print(f"API Calls Change:   {comparison['api_calls_change']:+,d}")
        print(f"Cache Hit Rate:     {current['cache_hit_rate']} "
              f"({comparison['cache_hit_rate_change']:+.1f}%)")
        print("=" * 80 + "\n")
        
        return comparison


def analyze_logs(log_dir='./logs/bandwidth', days=7):
    """
    Analyze bandwidth logs over multiple days.
    
    Args:
        log_dir: Directory containing bandwidth logs
        days: Number of days to analyze
    """
    log_path = Path(log_dir)
    if not log_path.exists():
        print(f"Log directory not found: {log_dir}")
        return
    
    # Find all metrics files
    metrics_files = sorted(log_path.glob('metrics_*.json'))
    
    if not metrics_files:
        print("No metrics files found")
        return
    
    # Load and aggregate
    total_bandwidth = 0
    total_calls = 0
    total_cache_hits = 0
    daily_stats = []
    
    for metrics_file in metrics_files[-days:]:
        with open(metrics_file, 'r') as f:
            data = json.load(f)
            session = data['session']
            daily_stats.append({
                'date': session['session_id'][:8],
                'bandwidth': session['total_bandwidth'],
                'calls': session['api_calls'],
                'cache_hits': session['cache_hits']
            })
            total_bandwidth += session['total_bandwidth']
            total_calls += session['api_calls']
            total_cache_hits += session['cache_hits']
    
    # Print analysis
    print("\n" + "=" * 80)
    print(f"MULTI-DAY BANDWIDTH ANALYSIS (Last {len(daily_stats)} sessions)")
    print("=" * 80)
    print(f"Total Bandwidth:    {BandwidthMonitor()._format_bytes(total_bandwidth)}")
    print(f"Total API Calls:    {total_calls:,}")
    print(f"Total Cache Hits:   {total_cache_hits:,}")
    print(f"Avg per Day:        {BandwidthMonitor()._format_bytes(total_bandwidth / len(daily_stats))}")
    print("")
    print("Daily Breakdown:")
    print("-" * 80)
    for stat in daily_stats:
        date_str = datetime.strptime(stat['date'], '%Y%m%d').strftime('%Y-%m-%d')
        print(f"{date_str} | {BandwidthMonitor()._format_bytes(stat['bandwidth']):>12s} | "
              f"{stat['calls']:>6d} calls | {stat['cache_hits']:>6d} cache hits")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    # Example usage
    monitor = BandwidthMonitor()
    
    # Simulate some operations
    monitor.log_api_call('AAPL', 'historical-price-full', 500, 15000, is_incremental=True, records_fetched=1)
    monitor.log_cache_hit('MSFT', 'profile', 'fresh')
    monitor.log_api_call('GOOGL', 'quote', 200, 800, records_fetched=1)
    monitor.log_ticker_skipped('TSLA', 'weekend')
    monitor.log_ticker_updated('AAPL', 15500)
    
    # Generate report
    monitor.generate_daily_report()
    monitor.save_metrics_json()
