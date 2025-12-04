import time
import statistics
import numpy as np

import dns.resolver

from rich.console import Console

DOMAIN = [
    "google.com"
]
SERVER = [
    "8.8.8.8",
    "1.1.1.1",
    "default"
]
def benchmark(console: Console,  additional_domains: list[str], N = 50) -> float:
    """
    My function makes square roots.

    Args:
        n: A number of some kind.

    Returns:
        The squarest root.
    """

    all_domains_to_benchmark = DOMAIN + additional_domains
    # console.print(all_domains_to_benchmark)

    all_servers_to_benchmark = SERVER
    # console.print(all_domains_to_benchmark)

    benchmark_bucket = {}
    benchmark_server_bucket = {}

    for server in all_servers_to_benchmark:
        benchmark_bucket[server] = {}
        benchmark_server_bucket[server] = []

    for server in all_servers_to_benchmark:
        for host in all_domains_to_benchmark:
            benchmark_bucket[server][host] = []
        
    for i in range(N):
        for server in all_servers_to_benchmark:
            for host in all_domains_to_benchmark:
                if server != "default":
                    msg = dns.message.make_query(host, "A")
                    start = time.perf_counter_ns()
                    dns.query.udp(msg, server)
                    end = time.perf_counter_ns()
                else:
                    start = time.perf_counter_ns()
                    dns.resolver.resolve(host, 'A')
                    end = time.perf_counter_ns()
                benchmark_bucket[server][host].append(end - start)
                benchmark_server_bucket[server].append(end - start)
        pass
    data = humanize_server_bucket(benchmark_server_bucket, roundoff_decimals = 3)
    return data

def humanize_server_bucket(server_bucket, roundoff_decimals = 5):
    server_bucket_npy = {server: np.array(latency) for server, latency in server_bucket.items() }
    server_bucket_sec = {server: latency / 1e9 for server, latency in server_bucket_npy.items() }
    server_bucket_sec_without_outliers = {server: reject_outliers(latency) for server, latency in server_bucket_sec.items() }
    return [ 
        {
            "server": server, 
            "mean": np.round(latency.mean(), decimals=roundoff_decimals), 
            "max": np.round(latency.max(), decimals=roundoff_decimals), 
            "min": np.round(latency.min(), decimals=roundoff_decimals), 
            "stddev": np.round(latency.std(), decimals=roundoff_decimals), 
            "p99": np.round(np.percentile(latency, 99), decimals=roundoff_decimals),
            "p95": np.round(np.percentile(latency, 95), decimals=roundoff_decimals),
        } for server, latency in server_bucket_sec_without_outliers.items() 
    ]

def reject_outliers(data, iqr=0.9):
    lower_percentile = (1 - iqr) / 2 
    upper_percentile = 1 - (1 - iqr) / 2 

    # Calculate Q1 and Q3
    q1 = np.percentile(data, 100 * lower_percentile)
    q3 = np.percentile(data, 100 * upper_percentile)

    # Calculate IQR
    iqr = q3 - q1

    # Define outlier bounds
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    # Identify outliers
    outliers = data[(data < lower_bound) | (data > upper_bound)]
    iqr_data = data[(data > lower_bound) & (data < upper_bound)]

    return iqr_data

def make_table():
    # # 3. Create the table
    # table = Table(title="Sorted Users by Last Name")
    # table.add_column("Server", style="cyan")
    # table.add_column("Min", justify="right", style="green")
    # table.add_column("Mean", style="magenta")
    # table.add_column("Std Dev", style="magenta")
    # table.add_column("Max", justify="left", style="green")
    # table.add_column("P95", justify="left", style="green")
    # table.add_column("P99", justify="left", style="green")

    # # 4. Add the *sorted* rows to the table
    # for data in sorted_data:
    #     table.add_row(
    #         data["server"],
    #         str(data["min"]),
    #         str(data["mean"]),
    #         str(data["stddev"]),
    #         str(data["max"]),
    #         str(data["p95"]),
    #         str(data["p99"])
    #     )
    pass
