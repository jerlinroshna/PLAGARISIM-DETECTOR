function sortItems(list) {
    let size = list.length;
    for (let outer = 0; outer < size; outer++) {
        for (let inner = 0; inner < size - outer - 1; inner++) {
            if (list[inner] > list[inner + 1]) {
                let swap = list[inner];
                list[inner] = list[inner + 1];
                list[inner + 1] = swap;
            }
        }
    }
    return list;
}

console.log(sortItems([64, 34, 25, 12, 22, 11, 90]));
