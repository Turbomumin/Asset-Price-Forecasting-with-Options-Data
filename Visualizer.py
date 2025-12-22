import seaborn as sns
import matplotlib.pyplot as plt
sns.set_theme(style="whitegrid")

def expiry_and_strike_graph(options_df, spot):
    fig, ax = plt.subplots(figsize=(7, 6))
    sns.scatterplot(
        data=options_df,
        x="days_to_expiry",
        y="strike",
        hue="option_type",
        palette={"C": "blue", "P": "red"},
        alpha=0.6,
        s=20,
        ax=ax
    )

    ax.axhline(spot, color="black", linestyle="--", linewidth=1)
    ax.set_xlabel("Days to expiry")
    ax.set_ylabel("Strike")
    ax.set_title("Option strikes vs time to expiry")

    plt.tight_layout()
    plt.show()
