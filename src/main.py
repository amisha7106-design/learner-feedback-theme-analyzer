from .database import FeedbackDatabase
from .analyzer import FeedbackAnalyzer


def main():

    print("\n================================")
    print(" LEARNER FEEDBACK THEME ANALYZER")
    print("================================")

    try:
        # Step 1: Initialize database
        print("\nStep 1: Connecting to database...")

        database = FeedbackDatabase()

        print("Database connected successfully!")

        # Step 2: Initialize analyzer
        print("\nStep 2: Initializing NLP analyzer...")

        analyzer = FeedbackAnalyzer(database)

        print("NLP analyzer initialized successfully!")

        # Step 3: Run feedback analysis
        print("\nStep 3: Running feedback analysis...")

        result = analyzer.run_analysis(max_clusters=5)

        # Step 4: Display analysis summary
        print("\n================================")
        print("       ANALYSIS SUMMARY")
        print("================================")

        print("Total Processed:", result["processed"])
        print("Positive Feedback:", result["positive"])
        print("Negative Feedback:", result["negative"])
        print("Neutral Feedback:", result["neutral"])

        # Step 5: Display identified themes
        print("\n================================")
        print("       IDENTIFIED THEMES")
        print("================================")

        for theme in result["themes"]:
            print("\nTheme:", theme["theme_name"])
            print("Keywords:", theme["keywords"])
            print("Feedback Count:", theme["feedback_count"])

        print("\n================================")
        print(" ANALYSIS COMPLETED SUCCESSFULLY")
        print("================================")

    except ValueError as error:
        print("\nAnalysis Error:", error)

    except Exception as error:
        print("\nUnexpected Error:", error)


if __name__ == "__main__":
    main()