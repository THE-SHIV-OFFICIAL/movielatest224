
import asyncio
import re
from database.ia_filterdb import Media, Media2, get_search_results
from info import DATABASE_URI, DATABASE_URI2, DATABASE_NAME, COLLECTION_NAME
from motor.motor_asyncio import AsyncIOMotorClient

async def check_database_status():
    """Check database status and file counts"""
    print("🔍 Checking Database Status...")
    print("=" * 50)

    # Count files in both databases
    media1_count = await Media.count_documents({})
    media2_count = await Media2.count_documents({})

    print(f"📊 Primary Database (Media): {media1_count} files")
    print(f"📊 Secondary Database (Media2): {media2_count} files")
    print(f"📊 Total Files: {media1_count + media2_count}")
    print()

async def check_duplicates():
    """Check for duplicate files across databases"""
    print("🔍 Checking for Duplicate Files...")
    print("=" * 50)

    # Get all file_ids from both databases
    media1_cursor = Media.find({}, {"file_id": 1, "file_name": 1})
    media2_cursor = Media2.find({}, {"file_id": 1, "file_name": 1})

    media1_files = await media1_cursor.to_list(length=None)
    media2_files = await media2_cursor.to_list(length=None)

    # Create sets of file_ids
    media1_ids = {file.file_id for file in media1_files}
    media2_ids = {file.file_id for file in media2_files}

    # Find duplicates
    duplicates = media1_ids.intersection(media2_ids)

    print(f"🔄 Duplicate Files Found: {len(duplicates)}")

    if duplicates:
        print("\n📝 Sample Duplicate Files:")
        count = 0
        for file_id in duplicates:
            if count >= 10:  # Show only first 10
                print(f"... and {len(duplicates) - 10} more")
                break
            # Find file name for this file_id
            for file in media1_files:
                if file.file_id == file_id:
                    print(f"   - {file.file_name}")
                    break
            count += 1
    print()

async def test_search_query(query):
    """Test search query for duplicates"""
    print(f"🔍 Testing Search Query: '{query}'")
    print("=" * 50)

    files, next_offset, total_results = await get_search_results(
        chat_id=None, 
        query=query, 
        max_results=20
    )

    print(f"📊 Total Results: {total_results}")
    print(f"📊 Files Returned: {len(files)}")

    # Check for duplicates in results
    file_ids = [file.file_id for file in files]
    unique_file_ids = set(file_ids)

    if len(file_ids) != len(unique_file_ids):
        print(f"⚠️  Duplicate Results Found: {len(file_ids) - len(unique_file_ids)} duplicates")
    else:
        print("✅ No duplicate results found")

    print("\n📝 Search Results:")
    for i, file in enumerate(files[:10], 1):  # Show first 10 results
        print(f"   {i}. {file.file_name} (ID: {file.file_id[:20]}...)")

    if len(files) > 10:
        print(f"   ... and {len(files) - 10} more files")
    print()

async def find_files_by_pattern(pattern):
    """Find files matching a specific pattern"""
    print(f"🔍 Finding Files with Pattern: '{pattern}'")
    print("=" * 50)

    try:
        regex = re.compile(pattern, flags=re.IGNORECASE)
        filter_query = {'file_name': regex}

        # Search in both databases
        media1_cursor = Media.find(filter_query, {"file_id": 1, "file_name": 1})
        media2_cursor = Media2.find(filter_query, {"file_id": 1, "file_name": 1})

        media1_files = await media1_cursor.to_list(length=None)
        media2_files = await media2_cursor.to_list(length=None)

        print(f"📊 Found in Primary DB: {len(media1_files)} files")
        print(f"📊 Found in Secondary DB: {len(media2_files)} files")

        # Combine and show results
        all_files = media1_files + media2_files

        print(f"\n📝 Sample Files Found:")
        for i, file in enumerate(all_files[:20], 1):  # Show first 20
            db_source = "Primary" if file in media1_files else "Secondary"
            print(f"   {i}. {file.file_name} ({db_source} DB)")

        if len(all_files) > 20:
            print(f"   ... and {len(all_files) - 20} more files")

    except Exception as e:
        print(f"❌ Error searching for pattern: {e}")
    print()

async def cleanup_duplicates():
    """Remove duplicate files from secondary database"""
    print("🧹 Cleaning Up Duplicate Files...")
    print("=" * 50)

    # Get all file_ids from both databases
    media1_cursor = Media.find({}, {"file_id": 1})
    media1_files = await media1_cursor.to_list(length=None)
    media1_ids = {file.file_id for file in media1_files}

    # Find duplicates in secondary database
    media2_cursor = Media2.find({"file_id": {"$in": list(media1_ids)}})
    duplicates = await media2_cursor.to_list(length=None)

    print(f"🔄 Found {len(duplicates)} duplicates to remove from secondary DB")

    if duplicates:
        # Remove duplicates
        duplicate_ids = [dup.file_id for dup in duplicates]
        result = await Media2.delete_many({"file_id": {"$in": duplicate_ids}})
        print(f"✅ Removed {result.deleted_count} duplicate files from secondary database")
    else:
        print("✅ No duplicates found to remove")
    print()

async def main():
    """Main function to run all checks"""
    print("🤖 File Indexing Checker")
    print("=" * 50)

    # Initialize database connections
    await Media.ensure_indexes()
    await Media2.ensure_indexes()

    while True:
        print("\nSelect an option:")
        print("1. Check database status")
        print("2. Check for duplicates")
        print("3. Test search query")
        print("4. Find files by pattern")
        print("5. Cleanup duplicates")
        print("6. Exit")

        choice = input("\nEnter your choice (1-6): ").strip()

        if choice == "1":
            await check_database_status()

        elif choice == "2":
            await check_duplicates()

        elif choice == "3":
            query = input("Enter search query: ").strip()
            if query:
                await test_search_query(query)
            else:
                print("❌ Empty query provided")

        elif choice == "4":
            pattern = input("Enter file pattern to search: ").strip()
            if pattern:
                await find_files_by_pattern(pattern)
            else:
                print("❌ Empty pattern provided")

        elif choice == "5":
            confirm = input("Are you sure you want to cleanup duplicates? (yes/no): ").strip().lower()
            if confirm == "yes":
                await cleanup_duplicates()
            else:
                print("❌ Cleanup cancelled")

        elif choice == "6":
            print("👋 Goodbye!")
            break

        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    asyncio.run(main())
