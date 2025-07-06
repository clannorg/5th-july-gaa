#!/usr/bin/env python3
"""
Script 3: Combine All Clip Descriptions into One Big Text File
Simple concatenation of all txt files from the clips analysis
"""

from pathlib import Path

def combine_all_clips():
    """Combine all clip description txt files into one big text file"""
    
    # Input directory with all the txt files
    clips_dir = Path("results/halftime_detection/clips")
    
    if not clips_dir.exists():
        print(f"❌ Clips directory not found: {clips_dir}")
        return
    
    # Find all txt files
    txt_files = sorted([f for f in clips_dir.glob("*.txt") if f.name.startswith("clip_")])
    
    if not txt_files:
        print("❌ No clip txt files found!")
        return
    
    print(f"📁 Found {len(txt_files)} clip description files")
    
    # Output file
    output_file = Path("results/halftime_detection/all_clips_combined.txt")
    
    print(f"🔄 Combining all descriptions into {output_file}...")
    
    with open(output_file, 'w') as outfile:
        for i, txt_file in enumerate(txt_files):
            print(f"📄 Adding {txt_file.name} ({i+1}/{len(txt_files)})")
            
            # Add separator
            outfile.write(f"\n{'='*80}\n")
            outfile.write(f"FILE: {txt_file.name}\n")
            outfile.write(f"{'='*80}\n\n")
            
            # Add file content
            with open(txt_file, 'r') as infile:
                outfile.write(infile.read())
            
            outfile.write("\n\n")
    
    print(f"✅ Combined file saved to: {output_file}")
    
    # Show file size
    file_size = output_file.stat().st_size
    print(f"📊 File size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
    
    return output_file

def main():
    print("🗂️  COMBINE ALL CLIP DESCRIPTIONS")
    print("=" * 50)
    print("Combining all txt files into one big text file...")
    print()
    
    output_file = combine_all_clips()
    
    if output_file:
        print(f"\n🎉 SUCCESS!")
        print(f"📁 All clip descriptions combined into: {output_file}")

if __name__ == "__main__":
    main() 