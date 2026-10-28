public class RenamedFactorial {
    public static long compute(int count) {
        long total = 1;
        for (int step = 1; step <= count; step++) {
            total = total * step;
        }
        return total;
    }

    public static void main(String[] arguments) {
        System.out.println("Result: " + compute(5));
    }
}
