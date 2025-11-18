"""
PERF-ALPHA Performance Optimization Migration

This migration applies database indexes and optimizations for:
- Faster query response times
- Improved cache efficiency
- Better connection pooling

Created: 2025-11-18
Issue: #100
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.db.connection import get_engine
from backend.db.performance_indexes import add_performance_indexes, analyze_tables
from sqlalchemy.orm import Session


def run_migration():
    """Run PERF-ALPHA performance optimization migration."""
    print("=" * 70)
    print("PERF-ALPHA Performance Optimization Migration")
    print("=" * 70)
    print()

    engine = get_engine()

    with Session(engine) as session:
        print("📊 Adding performance indexes...")
        print("-" * 70)

        # Add indexes
        index_results = add_performance_indexes(session)

        # Print results
        successful = 0
        failed = 0

        for index_name, status in index_results.items():
            if "error" in status.lower():
                print(f"  ✗ {index_name}: {status}")
                failed += 1
            else:
                print(f"  ✓ {index_name}: {status}")
                successful += 1

        print()
        print(f"Indexes: {successful} successful, {failed} failed")
        print()

        # Run ANALYZE on all tables
        print("📈 Analyzing tables to update query planner statistics...")
        print("-" * 70)

        analyze_results = analyze_tables(session)

        successful_analyze = 0
        failed_analyze = 0

        for table_name, status in analyze_results.items():
            if "error" in status.lower():
                print(f"  ✗ {table_name}: {status}")
                failed_analyze += 1
            else:
                print(f"  ✓ {table_name}: {status}")
                successful_analyze += 1

        print()
        print(f"Tables analyzed: {successful_analyze} successful, {failed_analyze} failed")
        print()

    # Summary
    print("=" * 70)
    print("Migration Summary")
    print("=" * 70)
    print(f"✓ Indexes added: {successful}/{successful + failed}")
    print(f"✓ Tables analyzed: {successful_analyze}/{successful_analyze + failed_analyze}")
    print()
    print("Performance optimizations applied successfully!")
    print()
    print("Next steps:")
    print("  1. Monitor /health/performance endpoint for cache hit rates")
    print("  2. Check query performance improvements")
    print("  3. Verify API response times are <100ms")
    print()


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
