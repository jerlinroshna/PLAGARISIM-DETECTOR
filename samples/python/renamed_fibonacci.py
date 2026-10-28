def generate_series(count):
    if count <= 0:
        return []
    output_list = [0, 1]
    while len(output_list) < count:
        computed = output_list[-1] + output_list[-2]
        output_list.append(computed)
    return output_list[:count]

if __name__ == "__main__":
    final_data = generate_series(10)
    print("Computed series:", final_data)
