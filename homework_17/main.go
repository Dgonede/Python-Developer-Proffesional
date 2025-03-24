package main

import (
	"fmt"
	"log"
	"os"
	"sync"

	"github.com/bradfitz/gomemcache/memcache"
)

// Функция загрузки данных в Memcached
func loadDataToMemcache(client *memcache.Client, data map[string]string, wg *sync.WaitGroup) {
	defer wg.Done()
	for key, value := range data {
		err := client.Set(&memcache.Item{Key: key, Value: []byte(value)})
		if err != nil {
			log.Printf("Ошибка при загрузке %s в Memcache: %v\n", key, err)
		}
	}
}

// Разбиение данных на чанки
func chunkData(data map[string]string, chunkSize int) []map[string]string {
	var chunks []map[string]string
	chunk := make(map[string]string)

	for key, value := range data {
		if len(chunk) == chunkSize {
			chunks = append(chunks, chunk)
			chunk = make(map[string]string)
		}
		chunk[key] = value
	}

	if len(chunk) > 0 {
		chunks = append(chunks, chunk)
	}

	return chunks
}

// Загрузка всех данных в Memcached с использованием горутин
func loadAllData(data map[string]string, chunkSize int, maxWorkers int) {
	client := memcache.New("localhost:11211")
	chunks := chunkData(data, chunkSize)

	var wg sync.WaitGroup

	for _, chunk := range chunks {
		wg.Add(1)
		go loadDataToMemcache(client, chunk, &wg)
	}

	wg.Wait()
	fmt.Println("Все данные загружены в Memcache.")
}

// Функция получения данных из Memcached и записи в файл
func getDataFromMemcache(client *memcache.Client, key string, file *os.File) {
	item, err := client.Get(key)
	if err != nil {
		log.Printf("Ошибка при получении %s: %v\n", key, err)
		return
	}
	result := fmt.Sprintf("Ключ: %s, Значение: %s\n", key, string(item.Value))
	fmt.Print(result)           // Вывод в консоль
	file.WriteString(result)    // Запись в файл
}

// Основная функция
func main() {
	data := map[string]string{
		"key1": "value1", "key2": "value2", "key3": "value3", "key4": "value4",
		"key5": "value5", "key6": "value6", "key7": "value7", "key8": "value8",
	}

	fmt.Println("Начинаем загрузку данных в Memcache...")
	loadAllData(data, 2, 4)

	// Открываем файл для записи результатов
	file, err := os.Create("result.txt")
	if err != nil {
		log.Fatalf("Ошибка при создании файла: %v", err)
	}
	defer file.Close()

	// Проверяем, загрузились ли данные
	client := memcache.New("localhost:11211")
	keys := []string{"key1", "key2", "key3", "key4", "key5", "key6", "key7", "key8"}
	for _, key := range keys {
		getDataFromMemcache(client, key, file)
	}

	fmt.Println("Результаты записаны в result.txt")
}